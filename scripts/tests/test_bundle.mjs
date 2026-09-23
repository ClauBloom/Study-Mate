import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath, pathToFileURL } from 'node:url';
import test from 'node:test';
import { findPython } from '../../bin/studymate.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const python = findPython();
const plugin = pathToFileURL(path.join(root, 'bin/dsh-plugin.mjs')).href;

function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'studymate-bundle-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const home = path.join(dir, "家 O'Brien #1");
  const dshHome = path.join(home, '.dsh');
  const workspace = path.join(home, '学习资料');
  const env = { ...process.env, HOME: home, USERPROFILE: home, DSH_HOME: dshHome, LEARN_WORKSPACE: workspace };
  const patch = path.join(dshHome, 'profiles', 'web', 'cordis.patch.yml');
  const config = path.join(dshHome, 'studymate-config.yaml');
  const engine = path.join(dshHome, 'studymate', 'engine');
  const run = (code, overrides = {}) => spawnSync(process.execPath, ['--input-type=module', '-e', code], {
    env: { ...env, ...overrides }, encoding: 'utf8', timeout: 30000,
  });
  function boot(overrides) {
    return run(`import { apply } from ${JSON.stringify(plugin)};
      const state = {registered: 0, disposed: 0};
      const effects = [];
      const ctx = {
        get: () => ({name: 'web', home: process.env.DSH_HOME}),
        agentPresets: {register: async config => {
          state.config = config; state.registered++;
          return async () => { state.disposed++; };
        }},
        effect: async fn => {effects.push(await fn());},
      };
      try {await apply(ctx); for (const dispose of effects) await dispose();}
      catch (error) {state.error = error.message; process.exitCode = 1;}
      console.log(JSON.stringify(state));`, overrides);
  }
  function yaml(file) {
    const result = spawnSync(python.command, [...python.prefix, '-c',
      'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1],encoding="utf-8"))))', file], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return JSON.parse(result.stdout);
  }
  return { dir, env, dshHome, workspace, patch, config, engine, run, boot, yaml };
}

test('native loading initializes portable skills and owns the preset lifetime without a dsh subprocess', t => {
  const f = fixture(t);
  const result = f.boot();
  assert.equal(result.status, 0, result.stderr + result.stdout);
  const state = JSON.parse(result.stdout);
  assert.equal(state.registered, 1);
  assert.equal(state.disposed, 1);
  assert.equal(state.config.id, 'learning');
  assert.deepEqual(state.config.plugins.find(row => row.id === 'tool-bash').disabled,
    { __jsExpr: "process.platform === 'win32'" });
  assert.deepEqual(state.config.plugins.find(row => row.id === 'skill-filesystem').config.customSkillDirs,
    [path.join(f.engine, '.dsh', 'skills').split(path.sep).join('/')]);
  const skills = fs.readFileSync(path.join(f.engine, '.dsh/skills/learning-system/SKILL.md'), 'utf8');
  assert.ok(skills.includes(process.platform === 'win32' ? 'PowerShell' : 'python'));
  assert.equal(fs.existsSync(f.patch), false);
  assert.equal(fs.existsSync(path.join(f.dshHome, '.agent-presets')), false);
  assert.equal(f.yaml(f.config).workspace, fs.realpathSync(f.workspace));
  const data = path.join(f.workspace, '.learning', 'subjects', 'keep.txt');
  fs.writeFileSync(data, 'my learning data');
  const config = { ...f.yaml(f.config), custom: 'keep' };
  fs.writeFileSync(f.config, JSON.stringify(config));
  fs.writeFileSync(path.join(f.engine, 'obsolete.txt'), 'old package');
  const again = f.boot({ LEARN_WORKSPACE: '' });
  assert.equal(again.status, 0, again.stderr + again.stdout);
  assert.equal(f.yaml(f.config).custom, 'keep');
  assert.equal(fs.readFileSync(data, 'utf8'), 'my learning data');
  assert.equal(fs.existsSync(path.join(f.engine, 'obsolete.txt')), false);
});

test('old managed registration migrates once, preserving other plugins and learning data', t => {
  const f = fixture(t);
  fs.mkdirSync(path.dirname(f.patch), { recursive: true });
  const original = '# unrelated plugin\n- id: keep\n  disabled: true\n';
  fs.writeFileSync(f.patch, original);
  const cliUrl = pathToFileURL(path.join(root, 'bin/studymate.mjs')).href;
  const installed = f.run(`import {installPayload} from ${JSON.stringify(cliUrl)};
    installPayload({version:'0.1.7-alpha.1'});`);
  assert.equal(installed.status, 0, installed.stderr);
  assert.match(fs.readFileSync(f.patch, 'utf8'), /BEGIN STUDYMATE/);
  const migrated = f.boot();
  assert.equal(migrated.status, 1);
  const state = JSON.parse(migrated.stdout);
  assert.match(state.error, /重启 DSH 一次/);
  assert.equal(state.registered, 0);
  assert.equal(fs.readFileSync(f.patch, 'utf8'), original);
  const restarted = f.boot();
  assert.equal(restarted.status, 0, restarted.stdout + restarted.stderr);
  assert.equal(JSON.parse(restarted.stdout).registered, 1);
  assert.equal(f.yaml(f.config).workspace, fs.realpathSync(f.workspace));
});

test('manual learning declarations fail without replacing existing data', t => {
  const f = fixture(t);
  assert.equal(f.boot().status, 0);
  const config = fs.readFileSync(f.config, 'utf8');
  fs.mkdirSync(path.dirname(f.patch), { recursive: true });
  const manual = '- insert:\n  - id: custom-learning\n    name: "@deepseek-ai/dsh-agent-preset"\n    config: {id: learning, plugins: []}\n';
  fs.writeFileSync(f.patch, manual);
  const failed = f.boot();
  assert.equal(failed.status, 1);
  assert.match(JSON.parse(failed.stdout).error, /learning/);
  assert.equal(fs.readFileSync(f.patch, 'utf8'), manual);
  assert.equal(fs.readFileSync(f.config, 'utf8'), config);
});

test('unavailable Python reports the prerequisite on every supported platform', () => {
  for (const platform of ['darwin', 'linux', 'win32']) {
    assert.throws(() => findPython(platform, () => ({ status: 1 })), /Python 3\.9\+ 和 PyYAML/);
  }
});

test('an old host skips unsupported native loading without blocking startup', async () => {
  const { apply } = await import(plugin);
  const warnings = [];
  const previousWarn = console.warn;
  console.warn = message => warnings.push(String(message));
  try {
    await apply({});
    await apply({ get: () => ({ name: 'web', home: '/unused' }) });
  } finally {
    console.warn = previousWarn;
  }
  assert.equal(warnings.length, 2);
  for (const warning of warnings) {
    assert.match(warning, /0\.1\.7-alpha\.1/);
    assert.match(warning, /npx @yunmiao\/studymate install/);
  }
});
