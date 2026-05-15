const { execSync } = require('child_process');
const net = require('net');
const fs = require('fs');
const path = require('path');

const CONTAINER = process.env.POSTGRES_CONTAINER || 'magnet-postgres';
const MAX_ATTEMPTS = parseInt(process.env.WAIT_FOR_DB_ATTEMPTS || '30', 10);
const INTERVAL_MS = parseInt(process.env.WAIT_FOR_DB_INTERVAL_MS || '2000', 10);

const color = {
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
};

function readEnv() {
  const envPath = path.join(__dirname, '..', '.env');
  if (!fs.existsSync(envPath)) return {};
  const result = {};
  for (const rawLine of fs.readFileSync(envPath, 'utf8').split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq === -1) continue;
    result[line.slice(0, eq).trim()] = line.slice(eq + 1).trim();
  }
  return result;
}

function pgIsReadyInContainer(user, db) {
  try {
    execSync(`docker exec ${CONTAINER} pg_isready -U ${user} -d ${db}`, {
      stdio: 'ignore',
    });
    return true;
  } catch {
    return false;
  }
}

function tcpProbe(host, port) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    const done = (ok) => {
      socket.destroy();
      resolve(ok);
    };
    socket.setTimeout(1500);
    socket.once('connect', () => done(true));
    socket.once('timeout', () => done(false));
    socket.once('error', () => done(false));
    socket.connect(port, host);
  });
}

async function main() {
  const env = readEnv();
  const host = env.DB_HOST || 'localhost';
  const port = parseInt(env.DB_PORT || '5433', 10);
  const user = env.DB_USER || 'postgres';
  const db = env.DB_NAME || 'magnet_dev';

  console.log(`⏳ Waiting for Postgres (container=${CONTAINER}, ${host}:${port}, db=${db})...`);

  for (let attempt = 1; attempt <= MAX_ATTEMPTS; attempt++) {
    if (pgIsReadyInContainer(user, db)) {
      console.log(color.green('✅ Postgres is ready (pg_isready).'));
      return;
    }
    if (await tcpProbe(host, port)) {
      console.log(color.green(`✅ Postgres TCP port ${host}:${port} is open.`));
      return;
    }
    console.log(color.yellow(`  ...not ready yet (${attempt}/${MAX_ATTEMPTS})`));
    await new Promise((r) => setTimeout(r, INTERVAL_MS));
  }

  console.error(color.red(`❌ Postgres did not become ready within ${(MAX_ATTEMPTS * INTERVAL_MS) / 1000}s.`));
  console.error(color.yellow(`   Hint: check 'docker ps' and 'docker logs ${CONTAINER}'.`));
  process.exit(1);
}

main();
