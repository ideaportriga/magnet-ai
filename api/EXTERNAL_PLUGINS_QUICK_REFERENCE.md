# 📋 Quick Reference: External Plugins Strategy

## 🎯 Recommended Approach for GitHub Publication

### ✅ What to do BEFORE publishing to GitHub:

```bash
# 1. Verify .gitignore excludes external plugins
git status
git ls-files src/plugins/external/
# Should only show: __init__.py and README.md files

# 2. Check for sensitive data in history
git log --all --full-history -- src/plugins/external/

# 3. If external plugins were previously committed, remove them:
git rm --cached src/plugins/external/knowledge_source/file.py
git rm --cached src/plugins/external/knowledge_source/fluidtopics.py
git commit -m "Remove client-specific plugins"
```

---

## 📦 Three Strategies for External Plugins

### 1️⃣ Separate Private Repositories ⭐ **RECOMMENDED**

**Best for:** Public GitHub repo + multiple clients

```bash
# Create private repo for each client plugin
magnet-plugins-file/
└── magnet_plugins_file/
    ├── __init__.py
    └── plugin.py

# Install in production
pip install git+https://${TOKEN}@github.com/org/magnet-plugins-file.git@v1.0.0
export MAGNET_PLUGINS=magnet_plugins_file.plugin

# Deploy with Docker
ENV MAGNET_PLUGINS=magnet_plugins_file.plugin
RUN pip install git+https://...
```

**Pros:**
- ✅ Complete code isolation
- ✅ Independent versioning
- ✅ Granular access control
- ✅ CI/CD friendly

---

### 2️⃣ Local External Directory

**Best for:** Development + private deployments

```bash
# Simply place plugins in external/ directory
api/src/plugins/external/knowledge_source/
├── __init__.py          # ✅ Committed
├── file.py             # ❌ .gitignored (client-specific)
└── fluidtopics.py      # ❌ .gitignored (client-specific)

# Plugins auto-load - no environment variables needed!
# .gitignore already configured to exclude them
```

**Pros:**
- ✅ Auto-loading (no env vars)
- ✅ Simple development
- ✅ No extra repos needed

**Cons:**
- ⚠️ Need external delivery mechanism for production
- ⚠️ Risk of accidental commit (mitigated by .gitignore)

---

### 3️⃣ Git Submodules

**Best for:** Experienced teams wanting tight integration

```bash
# Add private repo as submodule
git submodule add https://github.com/org/magnet-plugins-file.git \
    api/src/plugins/external/client_a

# .gitignore the submodule
echo "src/plugins/external/client_a/" >> .gitignore
```

**Pros:**
- ✅ All in one place for development
- ✅ Version tracking

**Cons:**
- ⚠️ Git complexity
- ⚠️ Easy to accidentally commit submodule ref

---

## 🚀 Quick Start: Separate Repos (Recommended)

### For Main Repo (Public)

```bash
# 1. Already done - .gitignore configured
cat api/.gitignore | grep "external"

# 2. Remove external plugins from git
git rm --cached src/plugins/external/knowledge_source/*.py

# 3. Commit and push
git commit -m "Prepare for public release"
git push origin main
```

### For External Plugin Repos (Private)

```bash
# 1. Create repo
mkdir magnet-plugins-file && cd magnet-plugins-file
git init
gh repo create magnet-plugins-file --private

# 2. Create structure
mkdir -p magnet_plugins_file
cat > setup.py << 'EOF'
from setuptools import setup, find_packages
setup(
    name="magnet-plugins-file",
    version="1.0.0",
    packages=find_packages(),
)
EOF

# 3. Copy plugin code
cp ../magnet-ai/api/src/plugins/external/knowledge_source/file.py \
   magnet_plugins_file/plugin.py

# 4. Create __init__.py with auto-registration
cat > magnet_plugins_file/__init__.py << 'EOF'
from magnet_plugins_file.plugin import FileUrlPlugin
EOF

# 5. Commit and tag
git add .
git commit -m "Initial version"
git tag v1.0.0
git push origin main --tags
```

### For Production Deployment

```dockerfile
# Dockerfile
FROM python:3.12

# Install main app
COPY api/ /app/api/
RUN pip install -e /app/api

# Install external plugin from private repo
ARG GITHUB_TOKEN
RUN pip install git+https://${GITHUB_TOKEN}@github.com/org/magnet-plugins-file.git@v1.0.0

ENV MAGNET_PLUGINS=magnet_plugins_file.plugin
CMD ["python", "api/run.py"]
```

```yaml
# docker-compose.yml
services:
  api:
    build:
      context: .
      args:
        GITHUB_TOKEN: ${GITHUB_TOKEN}
    environment:
      - MAGNET_PLUGINS=magnet_plugins_file.plugin
```

---

## 🔍 Verification Checklist

Before publishing to GitHub:

- [ ] `.gitignore` excludes `src/plugins/external/*/`
- [ ] Only `__init__.py` and `README.md` in external/ are committed
- [ ] No client-specific code in builtin/ plugins
- [ ] No hardcoded credentials anywhere
- [ ] `.env.example` doesn't contain sensitive data
- [ ] Git history doesn't contain removed plugin files
- [ ] README explains external plugin strategy

```bash
# Quick check
git ls-files api/src/plugins/external/
# Should output:
# api/src/plugins/external/README.md
# api/src/plugins/external/__init__.py
# api/src/plugins/external/knowledge_source/__init__.py
```

---

## 📚 Full Documentation

See **[EXTERNAL_PLUGINS_STRATEGY.md](./EXTERNAL_PLUGINS_STRATEGY.md)** for:
- Detailed comparison of all approaches
- Security best practices
- CI/CD integration examples
- Multi-client deployment strategies
- Troubleshooting guide

---

## 💡 Current State

**Builtin Plugins** (public, in main repo):
- ✅ Sharepoint, Sharepoint Pages
- ✅ Confluence
- ✅ Salesforce
- ✅ Oracle Knowledge
- ✅ RightNow
- ✅ Hubspot

**External Plugins** (client-specific, NOT in public repo):
- ❌ File (URL-based sources)
- ❌ FluidTopics

**Plugin Loading:**
- ✅ Builtin: Auto-loaded from `src/plugins/builtin/`
- ✅ External: Auto-loaded from `src/plugins/external/` (local)
- ✅ External: Loaded via `MAGNET_PLUGINS` env var (packages)

---

## 🎓 Examples

### Development Mode
```bash
# Just develop locally - plugins auto-load!
vim api/src/plugins/external/knowledge_source/my_plugin.py
python api/run.py  # Plugin automatically available
```

### Production with Separate Repos
```bash
# Install plugins
pip install git+https://${TOKEN}@github.com/org/magnet-plugins-file.git@v1.0.0
pip install git+https://${TOKEN}@github.com/org/magnet-plugins-fluidtopics.git@v1.0.0

# Configure
export MAGNET_PLUGINS=magnet_plugins_file.plugin,magnet_plugins_fluidtopics.plugin

# Run
python api/run.py
```

### CI/CD Pipeline
```yaml
# .github/workflows/deploy.yml
- name: Install plugins
  env:
    GH_TOKEN: ${{ secrets.PLUGIN_REPO_TOKEN }}
  run: |
    pip install git+https://${GH_TOKEN}@github.com/org/magnet-plugins-file.git@v1.0.0

- name: Deploy
  env:
    MAGNET_PLUGINS: magnet_plugins_file.plugin
  run: ./deploy.sh
```
