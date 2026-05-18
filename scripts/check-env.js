const fs = require('fs');
const path = require('path');

const envPath = path.join(__dirname, '..', '.env');
const examplePath = path.join(__dirname, '..', '.env.example');

// Mirrors `api/src/config/config.py::_validate_required` for the local-dev path
// (production also requires DATABASE_URL + SECRET_KEY, but we don't gate dev on those).
const REQUIRED_KEYS = ['SECRET_ENCRYPTION_KEY'];

// One of: DATABASE_URL OR the full DB_* component set.
const DB_COMPONENT_KEYS = [
  'DB_TYPE',
  'DB_HOST',
  'DB_PORT',
  'DB_NAME',
  'DB_USER',
  'DB_PASSWORD',
];

const color = {
  red: (s) => `\x1b[31m${s}\x1b[0m`,
  green: (s) => `\x1b[32m${s}\x1b[0m`,
  yellow: (s) => `\x1b[33m${s}\x1b[0m`,
};

function parseEnv(filePath) {
  const result = {};
  const content = fs.readFileSync(filePath, 'utf8');
  for (const rawLine of content.split('\n')) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#')) continue;
    const eq = line.indexOf('=');
    if (eq === -1) continue;
    const key = line.slice(0, eq).trim();
    let value = line.slice(eq + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    result[key] = value;
  }
  return result;
}

function ensureEnvFile() {
  if (fs.existsSync(envPath)) {
    console.log(color.green('✅ .env file exists.'));
    return;
  }
  console.warn(color.yellow('⚠️  .env file not found!'));
  if (!fs.existsSync(examplePath)) {
    console.error(color.red('❌ .env.example not found. Cannot create .env.'));
    process.exit(1);
  }
  console.log('Creating .env from .env.example...');
  fs.copyFileSync(examplePath, envPath);
  console.log(color.green('✅ .env created. Please review configuration.'));
}

function validateRequired() {
  const env = parseEnv(envPath);
  const errors = [];

  // 1. Unconditionally required (matches config.py)
  for (const key of REQUIRED_KEYS) {
    if (!env[key] || env[key].length === 0) {
      errors.push(`Missing required key '${key}'. Uncomment/set it in .env.`);
    }
  }

  // 2. Database connection: DATABASE_URL OR full DB_* set
  const hasDatabaseUrl = !!env.DATABASE_URL && env.DATABASE_URL.length > 0;
  if (!hasDatabaseUrl) {
    const missingDb = DB_COMPONENT_KEYS.filter((k) => !env[k] || env[k].length === 0);
    if (missingDb.length > 0) {
      errors.push(
        `Database not configured. Set DATABASE_URL or all of: ${DB_COMPONENT_KEYS.join(', ')} (missing: ${missingDb.join(', ')}).`,
      );
    }
  }

  if (errors.length === 0) {
    console.log(color.green('✅ .env validation passed.'));
    return;
  }

  console.error(color.red('❌ .env validation failed:'));
  for (const err of errors) {
    console.error(color.red(`   • ${err}`));
  }
  process.exit(1);
}

ensureEnvFile();
validateRequired();
