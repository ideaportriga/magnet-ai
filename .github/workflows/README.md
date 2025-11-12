# GitHub Actions Workflows

This document describes the configured GitHub Actions workflows for the Magnet AI project.

## 📋 Workflows Overview

### 1. CI - Linting and Tests (`ci.yml`)

**Triggers:**
- Push to `main` and `develop` branches
- Pull requests to `main` and `develop` branches
- Manual trigger

**What it checks:**
- ✅ **API (Python)**
  - Ruff linting (code style check)
  - Ruff formatting
  - Pytest tests with code coverage
  - Upload coverage reports to Codecov

- ✅ **Web (TypeScript/Vue)**
  - ESLint check (all projects via Nx)
  - TypeScript type checking
  - Prettier formatting
  - Tests with code coverage

- ✅ **Docker**
  - API image build check
  - Web image build check
  - Layer caching for speed

- ✅ **Security**
  - Python dependencies vulnerability check (Safety)
  - npm/yarn dependencies check (yarn audit)

---

### 2. PR - Code Quality Checks (`pr-checks.yml`)

**Triggers:**
- Opening, updating, or reopening a Pull Request

**Features:**
- 🎯 **Smart optimization**: runs checks only for changed files
- 🚀 **Parallel execution**: independent checks run simultaneously
- 📊 **Automatic comments**: adds coverage comments to PR
- 🏷️ **Automatic labels**: labels PR by size (XS, S, M, L, XL)
- ⚡ **Cancel outdated runs**: automatically cancels old checks on new push

**Checks:**
- API: Ruff lint, Ruff format, Pytest
- Web: ESLint, TypeScript, Prettier, Tests
- PR Size Check (change size analysis)

---

### 3. Auto Fix - Format & Lint (`auto-fix.yml`)

**Triggers:**
- Manual trigger from GitHub UI
- On schedule (every Sunday at 00:00 UTC)

**What it does:**
- 🔧 Automatically formats code (Ruff + Prettier)
- 🔧 Fixes auto-fixable linting issues
- 📝 Creates commit with changes
- 🚀 Pushes changes to current branch

**Usage:**
```bash
# Run manually via GitHub UI:
Actions → Auto Fix - Format & Lint → Run workflow
```

---

### 4. Deploy VitePress Docs (`deploy-docs.yml`)

Automatic deployment of VitePress documentation to GitHub Pages.

**Triggers:**
- Push to `main` with changes in documentation
- Manual trigger

**Setup:**

1. **Enable GitHub Pages in repository settings:**
   - Go to Settings → Pages
   - In "Source" section select "GitHub Actions"

2. **Configure base URL (if needed):**
   - Open `.github/workflows/deploy-docs.yml`
   - Change `HELP_BASE_URL` variable to desired value
   - Default is `/magnet-ai/` (repository name)
   - For custom domain, set to `/` or leave empty

**Commands for local development:**
```bash
cd web
yarn nx run magnet-docs:dev       # Start dev server
yarn nx run magnet-docs:build     # Build documentation
yarn nx run magnet-docs:preview   # Preview built documentation
```

**After deployment:**
Documentation will be available at `https://ideaportriga.github.io/magnet-ai/`

---

## 🚀 Quick Start

### Local Development

**Python API:**
```bash
cd api
poetry install
poetry run ruff check . --fix        # Fix linting issues
poetry run ruff format .             # Format code
poetry run pytest                    # Run tests
```

**Web:**
```bash
cd web
yarn install
yarn nx run-many --target=lint --all --fix    # ESLint fix
yarn prettier --write "**/*.{ts,tsx,js,jsx,vue,json,css,scss,md}"  # Prettier
yarn nx run-many --target=test --all         # Tests
```

**Or use root commands:**
```bash
npm run lint        # Lint entire project
npm run lint:api    # API only
npm run lint:web    # Web only
```

---

## 🔧 Configuration

### Required Secrets (Optional)

Add to `Settings → Secrets and variables → Actions`:

- `CODECOV_TOKEN` - for uploading coverage reports to Codecov (optional)

### Branch Protection Rules Setup

Recommended to add in `Settings → Branches → Branch protection rules` for `main`:

- ✅ Require a pull request before merging
- ✅ Require status checks to pass before merging
  - `API - Lint & Test`
  - `Web - Lint & Test`
  - `Docker - Build Check`
- ✅ Require branches to be up to date before merging
- ✅ Require conversation resolution before merging

---

## 📊 Monitoring and Debugging

### View Logs
```
GitHub → Actions → Select workflow → Select run → View logs
```

### Check Cache
```
GitHub → Actions → Caches
```

### Re-run Failed Jobs
```
GitHub → Actions → Failed run → Re-run failed jobs
```

---

## 🎯 Best Practices

1. **Before push**: run local linters
   ```bash
   npm run lint
   ```

2. **Commits**: use conventional commits
   ```
   feat: add new feature
   fix: fix bug
   style: formatting changes
   refactor: code refactoring
   test: add tests
   docs: update documentation
   ```

3. **Pull Requests**: 
   - Keep PRs small (< 500 lines of changes)
   - Verify all CI checks passed
   - Respond to reviewer comments

4. **Use Auto Fix**: for quick formatting fixes

---

## 🐛 Troubleshooting

### CI Fails on API Linting
```bash
cd api
poetry run ruff check . --fix
poetry run ruff format .
git add -A
git commit -m "style: fix linting issues"
```

### CI Fails on Web Linting
```bash
cd web
yarn nx run-many --target=lint --all --fix
yarn prettier --write "**/*.{ts,tsx,js,jsx,vue,json,css,scss,md}"
git add -A
git commit -m "style: fix linting issues"
```

### Tests Fail Locally but Not in CI (or Vice Versa)
- Check dependency versions
- Clear cache: `poetry cache clear . --all` or `yarn cache clean`
- Reinstall dependencies

### Docker Build Fails
```bash
# API
docker build -t test-api ./api

# Web  
docker build -f Dockerfile -t test-web .
```

---

## 📈 Future Improvements

Possible additions:

- [ ] Integration with SonarQube/SonarCloud for code quality analysis
- [ ] E2E tests with Cypress/Playwright
- [ ] Performance tests
- [ ] Automatic deploy to staging on merge to develop
- [ ] Automatic changelog generator
- [ ] Dependabot for automatic dependency updates
- [ ] Automated security scanning (Snyk, GitHub Security)

---

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [ESLint Documentation](https://eslint.org/)
- [Nx Documentation](https://nx.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
