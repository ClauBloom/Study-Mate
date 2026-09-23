// Keep the existing script-style Python tests: unittest discovery would run none.
import { readdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';

let failed = false;
function run(command, args) {
  console.log(`\n${command} ${args.join(' ')}`);
  const result = spawnSync(command, args, { stdio: 'inherit', env: { ...process.env, PYTHONUTF8: '1' } });
  if (result.error) console.error(result.error.message);
  failed ||= result.status !== 0;
}
for (const file of readdirSync('scripts/tests').filter(name => /^test_.*\.py$/.test(name)).sort()) {
  run('python', ['-X', 'utf8', `scripts/tests/${file}`]);
}
for (const file of ['quiz_dom_test.js', 'toc_dom_test.js']) run(process.execPath, [`scripts/tests/${file}`]);
run(process.execPath, ['--test', 'scripts/release/release.test.mjs']);
process.exitCode = failed ? 1 : 0;
