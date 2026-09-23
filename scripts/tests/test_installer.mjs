import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import test from 'node:test';
import { supportsDsh, findPython } from '../../bin/studymate.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const cli = path.join(root, 'bin/studymate.mjs');
const python = findPython();

function fixture(t) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'studymate-test-'));
  t.after(() => fs.rmSync(dir, { recursive: true, force: true }));
  const home = path.join(dir, "家 O'Brien #1");
  const bin = path.join(dir, 'bin');
  fs.mkdirSync(bin, { recursive: true });
  const env = { ...process.env, HOME: home, USERPROFILE: home, DSH_HOME: path.join(home, '.dsh') };
  delete env.LEARN_WORKSPACE;
  const pathKey = Object.keys(env).find(key => key.toLowerCase() === 'path') || 'PATH';
  env[pathKey] = bin + path.delimiter + (env[pathKey] || '');
  const preset = path.join(env.DSH_HOME, '.agent-presets', 'learning', 'agent.cordis.yml');
  const patch = path.join(env.DSH_HOME, 'profiles', 'web', 'cordis.patch.yml');
  const config = path.join(env.DSH_HOME, 'studymate-config.yaml');
  function version(value) {
    fs.writeFileSync(path.join(bin, process.platform === 'win32' ? 'dsh.cmd' : 'dsh'),
      process.platform === 'win32' ? `@echo ${value}\r\n` : `#!/bin/sh\nprintf '%s\\n' '${value}'\n`, { mode: 0o755 });
  }
  function install(...args) {
    return spawnSync(process.execPath, [cli, 'install', ...args], { env, encoding: 'utf8', timeout: 30000 });
  }
  function yaml(file) {
    const result = spawnSync(python.command, [...python.prefix, '-c',
      'import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1],encoding="utf-8"))))', file], { encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return JSON.parse(result.stdout);
  }
  version('0.1.7-alpha.1');
  return { dir, home, env, preset, patch, config, version, install, yaml };
}

test('minimum DSH prerelease is compared correctly', () => {
  for (const version of ['0.1.5-rc.2', '0.1.5-rc.10', '0.1.5', '0.1.6-alpha.1', '0.1.7-alpha.1']) assert.ok(supportsDsh(version), version);
  for (const version of ['0.1.4', '0.1.5-alpha.9', '0.1.5-rc.1', 'bad']) assert.equal(supportsDsh(version), false, version);
});

test('install, reinstall and downgrade preserve workspace and unrelated profile configuration', t => {
  const f = fixture(t);
  fs.mkdirSync(path.dirname(f.patch), { recursive: true });
  const original = '# my other plugin\n- id: user-plugin\n  disabled: true\n';
  fs.writeFileSync(f.patch, original);
  const workspace = path.join(f.dir, '学习 [1]');
  let result = f.install('--workspace', workspace);
  assert.equal(result.status, 0, result.stderr);
  let patch = fs.readFileSync(f.patch, 'utf8');
  assert.ok(patch.startsWith(original));
  const row = f.yaml(f.patch).find(row => row.insert)?.insert[0];
  assert.equal(row.name, '@deepseek-ai/dsh-agent-preset');
  assert.equal(row.config.id, 'learning');
  const plugins = [];
  function collect(value) {
    if (!value || typeof value !== 'object') return;
    if (value.id) plugins.push(value);
    for (const child of Object.values(value)) collect(child);
  }
  collect(row.config.plugins);
  assert.equal(plugins.find(plugin => plugin.id === 'workflow-ptc').name, '@deepseek-ai/dsh-workflow-ptc');
  assert.deepEqual(plugins.find(plugin => plugin.id === 'skill-filesystem').config.customSkillDirs,
    [path.join(f.env.DSH_HOME, 'studymate', 'engine', '.dsh', 'skills').split(path.sep).join('/')]);
  assert.match(fs.readFileSync(f.preset, 'utf8'), /@deepseek-ai\/dsh-workflow-ptc/);
  const config = f.yaml(f.config);
  config.custom = 'keep';
  fs.writeFileSync(f.config, JSON.stringify(config));
  result = f.install();
  assert.equal(result.status, 0, result.stderr);
  assert.equal(fs.readFileSync(f.patch, 'utf8'), patch);
  assert.equal(f.yaml(f.config).workspace, fs.realpathSync(workspace));
  assert.equal(f.yaml(f.config).custom, 'keep');
  for (const [version, workflow] of [['0.1.6-alpha.1', 'ptc'], ['0.1.5-rc.2', 'worker-thread']]) {
    f.version(version);
    result = f.install();
    assert.equal(result.status, 0, result.stderr);
    assert.equal(fs.readFileSync(f.patch, 'utf8').trim(), original.trim());
    assert.ok(fs.readFileSync(f.preset, 'utf8').includes(`@deepseek-ai/dsh-workflow-${workflow}`));
  }
});

test('invalid profile patch fails before replacing a working install', t => {
  const f = fixture(t);
  const result = f.install('--workspace', path.join(f.dir, 'workspace'));
  assert.equal(result.status, 0, result.stderr);
  const before = fs.readFileSync(f.preset, 'utf8');
  const config = fs.readFileSync(f.config, 'utf8');
  fs.writeFileSync(f.patch, 'not: [valid');
  const failed = f.install();
  assert.notEqual(failed.status, 0);
  assert.equal(fs.readFileSync(f.preset, 'utf8'), before);
  assert.equal(fs.readFileSync(f.config, 'utf8'), config);
  assert.equal(fs.readFileSync(f.patch, 'utf8'), 'not: [valid');
});

test('profile option registers only the selected profile and rejects traversal', t => {
  const f = fixture(t);
  assert.notEqual(f.install('--profile', '../outside').status, 0);
  assert.equal(fs.existsSync(f.config), false);
  const result = f.install('--profile', 'headless', '--workspace', path.join(f.dir, 'workspace'));
  assert.equal(result.status, 0, result.stderr);
  assert.equal(fs.existsSync(f.patch), false);
  assert.equal(f.yaml(path.join(f.env.DSH_HOME, 'profiles', 'headless', 'cordis.patch.yml'))[0].insert[0].config.id, 'learning');
});
