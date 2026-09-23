import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { spawnSync } from 'node:child_process';
import { addChangelog, bumpVersion, mergedPullRequests, notesFromChangelog, registryVersion,
  releaseNotes, releasePlan, validatePack, verifyPublished, verifyPublishOrder } from './release.mjs';

const repository = 'Miaotofu01/Study-Mate';
const name = '@yunmiao/studymate';
function fixture(t) {
  const cwd = mkdtempSync(join(tmpdir(), 'studymate-release-test-'));
  t.after(() => rmSync(cwd, { recursive: true, force: true }));
  const git = (...args) => {
    const result = spawnSync('git', ['-c', 'user.name=Release test', '-c', 'user.email=test@example.invalid', '-c', 'commit.gpgsign=false', '-c', 'tag.gpgsign=false', ...args], { cwd, encoding: 'utf8' });
    assert.equal(result.status, 0, result.stderr);
    return result.stdout.trim();
  };
  git('init', '-b', 'main');
  writeFileSync(join(cwd, 'package.json'), JSON.stringify({ name, version: '0.1.1' }));
  git('add', 'package.json');
  git('commit', '-m', '最初版本');
  return { cwd, git, commit(file, message) {
    writeFileSync(join(cwd, file), message);
    git('add', file);
    git('commit', '-m', message);
    return git('rev-parse', 'HEAD');
  } };
}

test('stable patch/minor/major increments and rejects non-release inputs', () => {
  assert.equal(bumpVersion('0.1.1', 'patch'), '0.1.2');
  assert.equal(bumpVersion('0.1.9', 'minor'), '0.2.0');
  assert.equal(bumpVersion('0.9.9', 'major'), '1.0.0');
  for (const [version, bump] of [['1.2.3-beta', 'patch'], ['01.2.3', 'minor'], ['1.2.3', '$(echo danger)']]) {
    assert.throws(() => bumpVersion(version, bump));
  }
});

test('ordinary Chinese commits, full bodies and merged PRs survive changelog generation', () => {
  const notes = releaseNotes({ version: '0.1.2', baseTag: 'v0.1', date: '2026-09-23',
    commits: [{ sha: 'a'.repeat(40), subject: '修复学习模式 <script>', body: '保留详细说明\n第二行\n\n## 嵌入标题' }],
    pulls: [{ number: 4, title: '适配新版本 [DSH]' }] });
  assert.match(notes, /修复学习模式 &lt;script&gt;/);
  assert.match(notes, /第二行/);
  assert.match(notes, /compare\/v0\.1\.\.\.v0\.1\.2/);
  assert.match(notes, /pull\/4/);
  const previous = '# 更新记录\n\n## 手写记录\n\n原有文字\n';
  const changelog = addChangelog(previous, '0.1.2', notes);
  assert.ok(changelog.endsWith(previous.slice('# 更新记录\n\n'.length)));
  assert.equal(notesFromChangelog(changelog, '0.1.2'), notes.trim());
  assert.throws(() => addChangelog(changelog, '0.1.2', notes), /already contains/);
  assert.throws(() => addChangelog('## [0.1.2](url)\n', '0.1.2', notes), /already contains/);
});

test('first release includes history; v0.1 legacy tag bounds later release history', t => {
  const repo = fixture(t);
  const initial = repo.git('rev-parse', 'HEAD');
  assert.equal(releasePlan(repo.cwd, initial, 'patch').commits.length, 1);
  repo.git('tag', 'v0.1');
  const source = repo.commit('feature.txt', '完善中文功能\n\n保留普通提交的多行说明');
  repo.git('tag', 'not-a-release');
  const plan = releasePlan(repo.cwd, source, 'patch');
  assert.equal(plan.version, '0.1.2');
  assert.equal(plan.baseTag, 'v0.1');
  assert.equal(plan.commits.length, 1);
  assert.match(plan.commits[0].body, /多行说明/);
  assert.throws(() => releasePlan(repo.cwd, initial, 'patch'), /No commits/);
});

test('re-running the same source resumes only a matching annotated release tag', t => {
  const repo = fixture(t);
  repo.git('tag', 'v0.1');
  const source = repo.commit('change.txt', '兼容新版');
  const plan = releasePlan(repo.cwd, source, 'patch');
  writeFileSync(join(repo.cwd, 'package.json'), JSON.stringify({ name, version: plan.version }));
  repo.git('add', 'package.json');
  repo.git('commit', '-m', 'chore(release): v0.1.2');
  const { commits, retry, ...metadata } = plan;
  repo.git('tag', '-a', plan.tag, '-m', `StudyMate release metadata\n${JSON.stringify(metadata)}`);
  const resumed = releasePlan(repo.cwd, source, 'patch');
  assert.equal(resumed.retry, true);
  assert.equal(resumed.commit, repo.git('rev-parse', 'HEAD'));
  repo.git('tag', '-d', plan.tag);
  repo.git('tag', plan.tag);
  assert.throws(() => releasePlan(repo.cwd, source, 'patch'), /not created by this workflow/);
});

test('a tagged release cannot smuggle untested source changes into a retry', t => {
  const repo = fixture(t);
  const source = repo.git('rev-parse', 'HEAD');
  const plan = releasePlan(repo.cwd, source, 'patch');
  repo.commit('unexpected.mjs', 'untested source');
  repo.git('tag', '-a', plan.tag, '-m', `StudyMate release metadata\n${JSON.stringify(plan)}`);
  assert.throws(() => releasePlan(repo.cwd, source, 'patch'), /outside release metadata/);
});

test('merged PR lookup paginates and deduplicates, excluding unmerged or other-base PRs', async () => {
  const pr = (number, more = {}) => ({ number, merged_at: '2026-09-23', base: { ref: 'main', repo: { full_name: repository } }, ...more });
  const called = [];
  const pulls = await mergedPullRequests([{ sha: 'a' }, { sha: 'b' }], async path => {
    called.push(path);
    if (path.includes('/a/') && path.endsWith('page=1')) return Array.from({ length: 100 }, () => pr(4));
    return [pr(5), pr(6, { merged_at: null }), pr(7, { base: { ref: 'develop', repo: { full_name: repository } } })];
  });
  assert.deepEqual(pulls.map(pr => pr.number).sort(), [4, 5]);
  assert.ok(called.some(path => path.includes('/a/') && path.endsWith('page=2')));
});

test('npm status distinguishes unpublished from registry failure and immutable content conflicts', async () => {
  assert.equal(await registryVersion('0.1.2', async () => ({ status: 404 })), null);
  await assert.rejects(registryVersion('0.1.2', async () => ({ status: 503, ok: false })), /unknown/);
  const remote = { name, version: '0.1.2', dist: { integrity: 'sha512-matching' } };
  const pack = { version: '0.1.2', integrity: 'sha512-matching' };
  verifyPublished(remote, pack);
  assert.throws(() => verifyPublished(remote, { ...pack, integrity: 'sha512-other' }), /different contents/);
  verifyPublishOrder('0.1.2', { version: '0.1.1' });
  assert.throws(() => verifyPublishOrder('0.1.2', { version: '0.1.3' }), /refusing to replace/);
  assert.throws(() => verifyPublishOrder('0.1.2', { version: '1.0.0-beta' }), /not a stable version/);
});

test('tarball inspection rejects personal workspace, credentials and incomplete payloads', () => {
  const files = ['package.json', 'README.md', 'cordis.patch.yml', 'bin/dsh-plugin.mjs', 'bin/studymate.mjs', 'bin/skill-compat.mjs',
    'preset/learning/agent.cordis.yml', 'scripts/install_preset.py', 'scripts/gen_home.py', '.dsh/skills/learning-system/SKILL.md',
    'schemas/subject.json', 'templates/home.html', 'docs/使用说明.md'];
  const pack = { name, version: '0.1.2', files: files.map(path => ({ path })) };
  validatePack(pack);
  for (const path of ['workspace/我的科目/private.md', '.npmrc', 'templates/.env', 'scripts/release/release.mjs']) {
    assert.throws(() => validatePack({ ...pack, files: [...pack.files, { path }] }), /Unexpected or private/);
  }
  assert.throws(() => validatePack({ ...pack, files: pack.files.filter(file => !file.path.startsWith('schemas/')) }), /missing schemas/);
  for (const required of ['cordis.patch.yml', 'bin/dsh-plugin.mjs']) {
    assert.throws(() => validatePack({ ...pack, files: pack.files.filter(file => file.path !== required) }),
      error => error.message === `npm tarball is missing ${required}.`);
  }
});

test('release CLI refuses local runs before touching repository or contacting registries', () => {
  const before = readFileSync(new URL('../../package.json', import.meta.url));
  const result = spawnSync(process.execPath, ['scripts/release/release.mjs', 'prepare'], {
    encoding: 'utf8', env: { ...process.env, GITHUB_ACTIONS: 'false' },
  });
  assert.equal(result.status, 1);
  assert.match(result.stderr, /only allowed/);
  assert.deepEqual(readFileSync(new URL('../../package.json', import.meta.url)), before);
});
