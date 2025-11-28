const fs = require('fs');
const path = require('path');

const envPath = path.join(__dirname, '..', '.env');
const examplePath = path.join(__dirname, '..', '.env.example');

if (!fs.existsSync(envPath)) {
  console.warn('\x1b[33m%s\x1b[0m', '⚠️  .env file not found!');
  if (fs.existsSync(examplePath)) {
    console.log('Creating .env from .env.example...');
    fs.copyFileSync(examplePath, envPath);
    console.log('\x1b[32m%s\x1b[0m', '✅ .env created. Please review configuration.');
  } else {
    console.error('\x1b[31m%s\x1b[0m', '❌ .env.example not found. Cannot create .env.');
    process.exit(1);
  }
} else {
  console.log('\x1b[32m%s\x1b[0m', '✅ .env file exists.');
}
