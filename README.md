# Magnet AI

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python Lint](https://github.com/YOUR_USERNAME/magnet-ai/workflows/Python%20Lint/badge.svg)](https://github.com/YOUR_USERNAME/magnet-ai/actions/workflows/python-lint.yml)
[![Frontend Lint](https://github.com/YOUR_USERNAME/magnet-ai/workflows/Frontend%20Lint/badge.svg)](https://github.com/YOUR_USERNAME/magnet-ai/actions/workflows/frontend-lint.yml)
[![License Check](https://github.com/YOUR_USERNAME/magnet-ai/workflows/License%20Check/badge.svg)](https://github.com/YOUR_USERNAME/magnet-ai/actions/workflows/license-check.yml)
[![Security Check](https://github.com/YOUR_USERNAME/magnet-ai/workflows/Security%20Check/badge.svg)](https://github.com/YOUR_USERNAME/magnet-ai/actions/workflows/security-check.yml)

> **Note**: Replace `YOUR_USERNAME` in badge URLs with your actual GitHub username or organization name.

AI-powered knowledge management platform with RAG capabilities.

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Development](#development)
- [CI/CD](#cicd)
- [Docker Deployment](#docker-deployment)
- [Contributing](#contributing)
- [Security](#security)
- [License](#license)

## ✨ Features

- **Plugin System**: Extensible knowledge source integrations (SharePoint, Confluence, Salesforce, etc.)
- **RAG Implementation**: LangChain-based retrieval augmented generation
- **Multi-LLM Support**: OpenAI, Azure OpenAI, Groq
- **Vector Search**: PostgreSQL with pgvector
- **Modern Stack**: Litestar (Python) + Vue.js (Nx monorepo)

## 🏗️ Architecture

**Monolithic Full-Stack Application**

- **Backend**: Litestar (async Python), SQLAlchemy, PostgreSQL + pgvector
- **Frontend**: Vue.js 3, Nx monorepo, Vite
- **AI/ML**: LangChain, multiple LLM providers
- **Deployment**: Docker, Docker Compose

See [Copilot Instructions](.github/copilot-instructions.md) for detailed architecture documentation.

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 16+ with pgvector extension
- Docker & Docker Compose (for containerized deployment)

### Quick Start with Docker

```bash
# First time setup (creates DB schema + loads fixtures)
./magnet.sh first-run

# Normal startup
./magnet.sh start

# View logs
./magnet.sh logs
```

### Local Development Setup

**Backend:**

```bash
cd api
poetry install
poetry shell

# Start database
make docker-up

# Run migrations
make db-upgrade

# Load sample data
make fixtures-load

# Start API server
poetry run python run.py
```

**Frontend:**

```bash
cd web
corepack enable
yarn install

# Start development servers
yarn nx dev magnet-admin
# or
yarn nx run-many --target=dev --projects=magnet-admin,magnet-panel
```

See detailed setup instructions in:
- [API README](api/README.md)
- [Web README](web/README.md)

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

All code changes are automatically checked for:

✅ **Code Quality**: Ruff (Python), ESLint (JavaScript/TypeScript)  
✅ **Type Safety**: MyPy (Python), vue-tsc (TypeScript)  
✅ **Security**: Bandit, Safety, npm audit, CodeQL, Trivy, TruffleHog  
✅ **License Compliance**: All dependencies verified as Apache 2.0 compatible  

**Documentation:**
- [CI/CD Overview](.github/CI_CD_IMPLEMENTATION.md)
- [Quick Start Guide](.github/QUICKSTART.md)
- [Full Documentation](.github/README.md)

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
- [LangChain](https://python.langchain.com/) - AI/ML orchestration
- [PostgreSQL](https://www.postgresql.org/) + [pgvector](https://github.com/pgvector/pgvector) - Vector database
- [Nx](https://nx.dev/) - Monorepo tooling

---

**Status**: Active Development  
**Version**: 1.0.0  
**Last Updated**: November 2025


