# Magnet AI

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Documentation](https://img.shields.io/badge/docs-online-brightgreen)](https://ideaportriga.github.io/magnet-ai/)
[![CI - Linting and Tests](https://github.com/ideaportriga/magnet-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ideaportriga/magnet-ai/actions/workflows/ci.yml)
[![Code Quality](https://github.com/ideaportriga/magnet-ai/actions/workflows/code-quality.yml/badge.svg)](https://github.com/ideaportriga/magnet-ai/actions/workflows/code-quality.yml)
[![Deploy VitePress Docs](https://github.com/ideaportriga/magnet-ai/actions/workflows/deploy-docs.yml/badge.svg)](https://github.com/ideaportriga/magnet-ai/actions/workflows/deploy-docs.yml)
![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python&logoColor=white)
![Vue.js](https://img.shields.io/badge/Vue.js-3.x-green?logo=vue.js&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.x-blue?logo=typescript&logoColor=white)


Magnet AI is a free, open-source, low-code platform for CRM consultants and application experts who understand the potential of Generative AI but aren't AI engineers.
Magnet AI users can rapidly create AI-powered features, even without Python skills. Magnet AI solutions natively integrate with Salesforce, Siebel, and can be embedded or integrated into other applications.


## 🚀 Getting Started

### Prerequisites

- **Node.js** (v18+)
- **Python** (v3.12+)
- **Docker** & **Docker Compose** (for containerized database)
- **Poetry** (Python dependency manager)

### 1. Setup

Run the setup script to install all dependencies (Python API, Web Frontend, and tooling).

```bash
# Installs root dependencies, API dependencies (poetry), and Web dependencies (npm)
npm install
npm run setup
```

### 2. Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and configure the necessary variables.
   - For local development with Docker, the defaults usually work.

### 3. Running the Application

#### Option A: Local Development with Docker (Recommended)

This runs the API and Web frontend locally, and automatically starts the database in Docker (Postgres + pgvector).

```bash
npm run dev:docker
```
*This starts the database, API (port 8000), and Web (port 3000).*

#### Option B: Local Development with External Database

If you prefer to run the database yourself (e.g. on a remote server or local installation) instead of using Docker:

1. **Prerequisites**:
   - PostgreSQL 16+
   - `pgvector` extension installed and enabled (`CREATE EXTENSION vector;`)

2. **Configuration**:
   - Update your `.env` file with your database connection details (`DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`).

3. **Run the App**:
   ```bash
   npm run dev
   ```

#### Option C: API Only

```bash
npm run dev:api
```

#### Option D: Web Only

```bash
npm run dev:web
```

### 4. Database Management

- **Create Migration**: `npm run db:migrate -- -m "message"`
- **Apply Migrations**: `npm run db:upgrade`
- **Reset Database**: `npm run db:reset` (Warning: Deletes data!)

### 5. Troubleshooting

- **Port Conflicts**: Ensure ports 5432 (Postgres), 8000 (API), and 3000 (Web) are free.
- **Windows**: Use PowerShell or Git Bash. If using CMD, ensure `npm` is in your PATH.


## 💻 Development

### Code Quality

This project uses automated checks for code quality, security, and license compliance:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run all checks locally
pre-commit run --all-files

# Python linting
cd api
poetry run ruff check src/
poetry run ruff format src/

# Frontend linting
cd web
yarn lint
yarn type-check
```

See [CI/CD Documentation](.github/README.md) for details.

### Project Structure

```
magnet-ai/
├── api/                 # Python backend (Litestar)
│   ├── src/
│   │   ├── core/       # Core domain models, DB, plugins
│   │   ├── routes/     # API endpoints
│   │   ├── services/   # Business logic
│   │   └── plugins/    # Knowledge source plugins
│   └── tests/
├── web/                # Frontend monorepo (Nx + Vue)
│   ├── apps/
│   │   ├── magnet-admin/   # Admin UI
│   │   ├── magnet-panel/   # User interface
│   │   └── magnet-docs/    # Documentation
│   └── packages/           # Shared libraries
├── .github/            # CI/CD workflows
└── docker/             # Docker configuration
```

## 🔄 CI/CD

Full automation configured for every commit and Pull Request:

### Main Checks
✅ **Code Quality**: Ruff (Python), ESLint + Prettier (TypeScript/Vue)  
✅ **Type Safety**: TypeScript type checking  
✅ **Testing**: Pytest (Python), Vitest (TypeScript)  
✅ **Security**: Safety (Python), yarn audit (npm), dependency review  
✅ **Docker**: Image build checks  
✅ **Code Complexity**: Radon (Python)  
✅ **License Compliance**: Dependabot for dependency updates

### Workflows
- **CI**: Full checks on every push and PR ([ci.yml](.github/workflows/ci.yml))
- **PR Checks**: Smart checks for changed files only ([pr-checks.yml](.github/workflows/pr-checks.yml))
- **Code Quality**: Advanced code quality analysis ([code-quality.yml](.github/workflows/code-quality.yml))
- **Auto Fix**: Automatic code formatting ([auto-fix.yml](.github/workflows/auto-fix.yml))
- **Release**: Semantic versioning and automatic releases ([release.yml](.github/workflows/release.yml))
- **Docs**: Automatic documentation deploy to GitHub Pages ([deploy-docs.yml](.github/workflows/deploy-docs.yml))

### Local Development
```bash
# Lint entire project
npm run lint

# API only
npm run lint:api

# Web only
npm run lint:web
```

**Complete documentation**: [.github/workflows/README.md](.github/workflows/README.md)

## 🐳 Docker Deployment

### Build Docker Image

```bash
# Standard build
docker build -t magnet-ai .

# With custom base path (if hosted on non-root path)
docker build --build-arg WEB_BASE_PATH=/apps/magnet-ai/ -t magnet-ai .
```

**Note**: `WEB_BASE_PATH` should start and end with `/` if specified.

### Run Docker Container

```bash
# Run with environment file
docker run -d -p 8000:8000 --env-file=.env magnet-ai

# Run with Docker Compose
docker-compose up -d
```

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Database
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=magnet_ai
DB_USER=postgres
DB_PASSWORD=your_password

# Authentication (optional for dev)
AUTH_ENABLED=false

# CORS (for local development)
CORS_OVERRIDE_ALLOWED_ORIGINS=http://localhost:5000,http://localhost:3000
```

See `.env.example` for complete configuration options.

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Install pre-commit hooks**: `pre-commit install`
4. **Make your changes** and ensure all checks pass
5. **Commit your changes**: `git commit -m 'Add amazing feature'`
6. **Push to the branch**: `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Contribution Guidelines

- All code must pass linting, type checking, and security scans
- Add tests for new features
- Update documentation as needed
- Add Apache 2.0 license headers to new files
- Ensure all dependencies are Apache 2.0 compatible

See [Contributing Guide](CONTRIBUTING.md) for detailed information (if exists).

## 🔒 Security

We take security seriously. Please report security vulnerabilities responsibly.

- **Security Policy**: See [SECURITY.md](SECURITY.md)
- **Report Vulnerabilities**: Email security@your-organization.com (update with actual)
- **Security Checks**: Automated scans run on every commit and weekly

### Security Features

- 🔒 Automated security scanning (Bandit, Safety, CodeQL, Trivy)
- 🔒 Secret detection (TruffleHog, detect-secrets)
- 🔒 Dependency vulnerability scanning
- 🔒 License compliance verification
- 🔒 Pre-commit security hooks

## 📄 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

All dependencies are verified to be Apache 2.0 compatible.

### Third-Party Licenses

- Python dependencies: See [License Check workflow](.github/workflows/license-check.yml)
- JavaScript dependencies: See [License Check workflow](.github/workflows/license-check.yml)

## 📚 Additional Documentation

- [**Online Documentation**](https://ideaportriga.github.io/magnet-ai/)
- [Plugin System](generated_docs/PLUGIN_SYSTEM.md)
- [External Plugins Strategy](generated_docs/EXTERNAL_PLUGINS_STRATEGY.md)
- [Database Fixtures Guide](generated_docs/FIXTURES_GUIDE.md)
- [Migration Guide](generated_docs/MIGRATION_GUIDE.md)
- [Architecture Documentation](.github/copilot-instructions.md)

## 🆘 Support

- **Documentation**: See `generated_docs/` folder
- **Issues**: [GitHub Issues](https://github.com/YOUR_USERNAME/magnet-ai/issues)
- **Security**: [SECURITY.md](SECURITY.md)

## 🙏 Acknowledgments

Built with:
- [Litestar](https://litestar.dev/) - Python web framework
- [Vue.js](https://vuejs.org/) - Frontend framework
- [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) - Vector database
- [Nx](https://nx.dev/) - Monorepo tooling

---

**Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: November 2025


