const fs = require('fs');
const path = require('path');

const configs = [
  {
    path: 'web/apps/@ipr/magnet-admin/public/config/main.json',
    content: {
      auth: {
        enabled: false
      },
      api: {
        aiBridge: {
          baseUrl: "http://localhost:8000"
        }
      },
      panel: {
        baseUrl: "https://localhost:7002/panel/"
      },
      admin: {
        baseUrl: "https://localhost:7000/admin/"
      }
    }
  },
  {
    path: 'web/apps/@ipr/magnet-panel/public/config/main.json',
    content: {
      theme: "siebel",
      auth: {
        enabled: false
      },
      api: {
        aiBridge: {
          baseUrl: "http://localhost:8000"
        }
      },
      panel: {
        baseUrl: "https://localhost:7002/panel/"
      },
      admin: {
        baseUrl: "https://localhost:7000/admin/"
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
