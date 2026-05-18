// Ensures `yarn` is available on PATH for npm scripts that shell out to it.
//
// Strategy:
//   1. If `yarn` already runs — done.
//   2. If `corepack` is available (Node 16-24 bundles it) — `corepack enable`,
//      which shims `yarn` to use the version pinned in web/package.json#packageManager.
//   3. If `corepack` itself is missing (Node 25+ dropped the bundled binary),
//      install it via `npm i -g corepack@latest` and retry step 2.
//
// Exits 0 on success, 1 with a clear message on failure.

const { spawnSync } = require('child_process');

const color = {
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
};

const isWin = process.platform === 'win32';

function probe(cmd, args) {
  return spawnSync(cmd, args, { stdio: 'ignore', shell: isWin }).status === 0;
}

function run(cmd, args) {
  return spawnSync(cmd, args, { stdio: 'inherit', shell: isWin }).status === 0;
}

if (probe('yarn', ['--version'])) {
  console.log(color.green('✅ yarn is available.'));
  process.exit(0);
}

if (!probe('corepack', ['--version'])) {
  console.log(color.yellow('corepack not found — installing globally via npm...'));
  if (!run('npm', ['install', '-g', 'corepack@latest'])) {
    console.error(color.red('❌ Failed to install corepack via npm.'));
    console.error(color.yellow("   Try 'npm install -g corepack@latest' manually (may need sudo on system Node)."));
    process.exit(1);
  }
}

console.log(color.yellow('Activating yarn via corepack...'));
if (!run('corepack', ['enable'])) {
  console.error(color.red('❌ Failed to enable yarn via corepack.'));
  console.error(color.yellow("   Try 'corepack enable' manually (may need sudo on system Node)."));
  process.exit(1);
}

if (!probe('yarn', ['--version'])) {
  console.error(color.red('❌ yarn still not on PATH after corepack enable.'));
  console.error(color.yellow('   Open a new shell and re-run, or check your PATH.'));
  process.exit(1);
}

console.log(color.green('✅ yarn activated via corepack.'));
