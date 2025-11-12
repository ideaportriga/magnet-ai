# GitHub Actions Quick Start

## 🎯 What Was Configured

The following GitHub Actions workflows have been configured for your project:

### 1. CI - Main Checks (`ci.yml`)
- Runs on push and PR to `main` and `develop`
- Checks Python (Ruff) and Web (ESLint, TypeScript, Prettier)
- Runs tests with coverage
- Checks Docker images
- Scans dependencies for vulnerabilities

### 2. PR Checks - Smart Checks (`pr-checks.yml`)
- Optimized checks only for changed files
- Automatic coverage comments
- PR size labels (XS, S, M, L, XL)
- Parallel execution for speed

### 3. Code Quality - Extended Analysis (`code-quality.yml`)
- Conventional Commits check
- TODO/FIXME search
- Code complexity analysis
- Duplication check
- Performance hints

### 4. Auto Fix - Auto-correction (`auto-fix.yml`)
- Automatic code formatting
- Linting fixes
- Can be run manually or on schedule

### 5. Release - Automatic Releases (`release.yml`)
- Semantic versioning
- Automatic changelog generation
- GitHub Releases

### 6. Deploy Docs - Documentation Deployment (`deploy-docs.yml`)
- Automatic VitePress deployment to GitHub Pages

## 🚀 First Steps

### Step 1: Activate GitHub Actions

GitHub Actions should activate automatically after commit, but verify:

1. Go to GitHub: `https://github.com/ideaportriga/magnet-ai/actions`
2. Ensure workflows are visible
3. Enable workflows in Settings → Actions if needed

### Step 2: Configure Branch Protection (Recommended)

Protect the main branch from direct commits:

1. Settings → Branches → Add rule
2. Branch name pattern: `main`
3. Enable:
   - ☑️ Require a pull request before merging
   - ☑️ Require status checks to pass before merging
     - Select: `API - Lint & Test`, `Web - Lint & Test`, `Docker - Build Check`
   - ☑️ Require branches to be up to date before merging
   - ☑️ Require conversation resolution before merging

### Step 3: Configure GitHub Pages (for documentation)

1. Settings → Pages
2. Source: **GitHub Actions**
3. After first deployment, documentation will be available at:
   `https://ideaportriga.github.io/magnet-ai/`

### Step 4: Install pre-commit hooks (optional but recommended)

```bash
# In project root
pip install pre-commit
pre-commit install
```

Now checks will run locally before each commit.

### Step 5: Add Secrets (Optional)

For advanced features, add secrets in Settings → Secrets and variables → Actions:

- `CODECOV_TOKEN` - for coverage reports in Codecov (get from codecov.io)

## 📝 How to Use

### Daily Development

1. **Create a feature branch:**
   ```bash
   git checkout -b feature/my-feature
   ```

2. **Make changes and commit with conventional commits:**
   ```bash
   git add .
   git commit -m "feat: add new amazing feature"
   ```
   
   Commit types:
   - `feat:` - new feature
   - `fix:` - bug fix
   - `docs:` - documentation
   - `style:` - formatting
   - `refactor:` - refactoring
   - `test:` - tests
   - `chore:` - routine tasks

3. **Push and create PR:**
   ```bash
   git push origin feature/my-feature
   ```

4. **Create Pull Request on GitHub**
   - CI will automatically run all checks
   - Wait for green checkmarks
   - Request review from colleagues

### Automatic Formatting Fix

If CI fails on formatting checks:

**Locally:**
```bash
npm run lint
```

**Or via GitHub:**
1. Actions → Auto Fix - Format & Lint
2. Run workflow
3. Workflow will create a commit with fixes

### Creating a Release

**Automatically (semantic versioning):**
- Simply merge PR to `main`
- Semantic Release will automatically determine version from commits

**Manually:**
1. Actions → Release - Semantic Versioning
2. Run workflow
3. Enter version (e.g., `1.2.0`)

## 🔧 Troubleshooting

### CI Fails on API Linting

```bash
cd api
poetry install
poetry run ruff check . --fix
poetry run ruff format .
git add -A
git commit -m "style: fix linting issues"
git push
```

### CI Fails on Web Linting

```bash
cd web
yarn install
yarn nx run-many --target=lint --all --fix
yarn prettier --write "**/*.{ts,tsx,js,jsx,vue,json,css,scss,md}"
git add -A
git commit -m "style: fix linting issues"
git push
```

### Docker Build Fails

Check locally:
```bash
# API
cd api
docker build -t test-api .

# Web
cd ..
docker build -f Dockerfile -t test-web .
```

### Tests Fail

```bash
# Python tests
cd api
poetry run pytest -v

# Web tests
cd web
yarn nx run-many --target=test --all
```

## 📊 Monitoring

### View CI Status

Add badges to README (already added):
```markdown
[![CI - Linting and Tests](https://github.com/ideaportriga/magnet-ai/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/ideaportriga/magnet-ai/actions/workflows/ci.yml)
```

### View Logs

1. GitHub → Actions
2. Select workflow run
3. Click on failed job
4. View error details

### Cache

CI uses caching for speed:
- Poetry dependencies
- Yarn dependencies
- Docker layers

Clear cache: Settings → Actions → Caches → Delete

## 🎓 Best Practices

1. **Always check locally before push:**
   ```bash
   npm run lint
   ```

2. **Write meaningful commit messages:**
   ```bash
   feat: add user authentication
   fix: resolve memory leak in data processor
   docs: update API documentation
   ```

3. **Keep PRs small:**
   - Goal: < 500 lines of changes
   - CI will automatically label large PRs

4. **Respond to reviewer comments quickly**

5. **Don't merge PRs with failed checks**

6. **Use Auto Fix for quick formatting fixes**

## 📚 Additional Resources

- [Full Documentation](.github/workflows/README.md)
- [Badges for README](.github/BADGES.md)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)

## ✅ Readiness Checklist

- [ ] GitHub Actions activated
- [ ] Branch protection configured for `main`
- [ ] GitHub Pages configured
- [ ] Pre-commit hooks installed (optional)
- [ ] Badges added to README
- [ ] Team knows about Conventional Commits
- [ ] Dependabot enabled (already configured)

---

**Done!** 🎉 Your project now has a production-ready CI/CD pipeline.

All new PRs will be automatically checked, and you'll receive notifications about any issues before merging to main.
