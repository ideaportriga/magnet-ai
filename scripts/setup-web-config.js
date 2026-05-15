const fs = require('fs');
const path = require('path');

const configs = [
  {
    path: 'web/apps/@ipr/magnet-admin/public/config/main.json',
    content: {
      auth: {
        enabled: true,
        signupEnabled: false
      },
      api: {
        aiBridge: {
          // Empty baseUrl => frontend uses relative paths; Vite proxy in
          // vite.config.ts routes /api/* to http://localhost:8000.
          // Same-origin keeps auth cookies (SameSite=Lax + Secure) working.
          baseUrl: ""
        }
      },
      panel: {
        baseUrl: "https://localhost:7002/panel/"
      },
      admin: {
        baseUrl: "https://localhost:7001/admin/"
      }
    }
  },
  {
    path: 'web/apps/@ipr/magnet-panel/public/config/main.json',
    content: {
      theme: "siebel",
      auth: {
        enabled: true,
        signupEnabled: false
      },
      api: {
        aiBridge: {
          // Empty baseUrl => frontend uses relative paths; Vite proxy in
          // vite.config.ts routes /api/* to http://localhost:8000.
          // Same-origin keeps auth cookies (SameSite=Lax + Secure) working.
          baseUrl: ""
        }
      },
      panel: {
        baseUrl: "https://localhost:7002/panel/"
      },
      admin: {
        baseUrl: "https://localhost:7001/admin/"
      }
    }
  }
];

configs.forEach(config => {
  const fullPath = path.resolve(process.cwd(), config.path);
  const dir = path.dirname(fullPath);

  if (!fs.existsSync(dir)) {
    console.log(`Creating directory: ${dir}`);
    fs.mkdirSync(dir, { recursive: true });
  }

  if (!fs.existsSync(fullPath)) {
    console.log(`Creating config file: ${fullPath}`);
    fs.writeFileSync(fullPath, JSON.stringify(config.content, null, 2));
  } else {
    console.log(`Config file already exists: ${fullPath}`);
  }
});
