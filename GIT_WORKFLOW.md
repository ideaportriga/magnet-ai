# Git Workflow & CI/CD Guide

This document describes the branching strategy, release process, and CI/CD pipeline for Magnet AI.

## Table of Contents

- [Branching Strategy](#branching-strategy)
- [Commit Convention](#commit-convention)
- [CI/CD Pipeline Overview](#cicd-pipeline-overview)
- [Workflow Details](#workflow-details)
- [Docker Image Tags](#docker-image-tags)
- [Release Process](#release-process)

---

## Branching Strategy

We follow a simplified Git Flow model with two main branches:

| Branch | Purpose | Docker Tag | Protected |
|--------|---------|------------|-----------|
| `main` | Production-ready code | `latest`, `vX.Y.Z` | ✅ Yes |
| `develop` | Development integration | `dev` | ✅ Yes |

### Feature Development

```
main ─────────────────────────────────────────────────►
       │                                    ▲
       │                                    │ (merge via PR)
       ▼                                    │
develop ──────┬─────────────────────────────┴─────────►
              │              ▲
              │              │ (merge via PR)
              ▼              │
        feature/xyz ─────────┘
```

1. Create feature branches from `develop`
2. Open PR to `develop` when ready
3. After review and CI passes, merge to `develop`
4. Periodically, `develop` is merged to `main` for release

---

## Commit Convention

We use [Conventional Commits](https://www.conventionalcommits.org/) for automatic versioning:

| Prefix | Description | Version Bump |
|--------|-------------|--------------|
| `feat:` | New feature | Minor (1.X.0) |
| `fix:` | Bug fix | Patch (1.0.X) |
| `perf:` | Performance improvement | Patch (1.0.X) |
| `refactor:` | Code refactoring | Patch (1.0.X) |
| `docs:` | Documentation only | ❌ No release |
| `style:` | Code style (formatting) | ❌ No release |
| `test:` | Adding tests | ❌ No release |
| `chore:` | Maintenance tasks | ❌ No release |
| `ci:` | CI/CD changes | ❌ No release |

> **Note:** Both `main` and `develop` branches use semantic-release. The `develop` branch creates prerelease versions (`X.Y.Z-dev.N`), while `main` creates stable versions (`X.Y.Z`).

### Breaking Changes

Add `!` after type or include `BREAKING CHANGE:` in footer for major version bump:

```
feat!: remove deprecated API endpoints

BREAKING CHANGE: The /v1/chat endpoint has been removed. Use /v2/chat instead.
```

---

## CI/CD Pipeline Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DEVELOP BRANCH                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   git push develop (feat/fix commit)                                        │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────┐                                                   │
│   │   ci.yml            │  trigger: push (branches: develop)                │
│   │   "CI - Linting     │                                                   │
│   │    and Tests"       │                                                   │
│   └──────────┬──────────┘                                                   │
│              │                                                              │
│              │ workflow_run (conclusion: success)                           │
│              ▼                                                              │
│   ┌─────────────────────┐                                                   │
│   │   release.yml       │  → Runs semantic-release                          │
│   │                     │  → Creates prerelease version                     │
│   └──────────┬──────────┘                                                   │
│              │                                                              │
│              │ (if releasable commits)                                      │
│              ▼                                                              │
│   ┌─────────────────────┐                                                   │
│   │  docker-publish.yml │  → Build & Push                                   │
│   │                     │  → Tags: `dev`, `1.2.0-dev.1`, `v1.2.0-dev.1`     │
│   └─────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                               MAIN BRANCH                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│   git push main (or merge PR from develop)                                  │
│         │                                                                   │
│         ▼                                                                   │
│   ┌─────────────────────┐                                                   │
│   │   ci.yml            │  trigger: push (branches: main)                   │
│   │   "CI - Linting     │                                                   │
│   │    and Tests"       │                                                   │
│   └──────────┬──────────┘                                                   │
│              │                                                              │
│              │ workflow_run (conclusion: success)                           │
│              ▼                                                              │
│   ┌─────────────────────┐                                                   │
│   │   release.yml       │  → Runs semantic-release                          │
│   │                     │  → Creates stable release                         │
│   └──────────┬──────────┘                                                   │
│              │                                                              │
│              │ (if releasable commits)                                      │
│              ▼                                                              │
│   ┌─────────────────────┐                                                   │
│   │  docker-publish.yml │  → Build & Push                                   │
│   │                     │  → Tags: `latest`, `1.2.0`, `v1.2.0`              │
│   └─────────────────────┘                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Workflow Details

### 1. CI Workflow (`ci.yml`)

**Trigger:** Push to `main` or `develop`

| Job | Description |
|-----|-------------|
| `api-checks` | Python linting (Ruff), format check |
| `web-checks` | ESLint for Vue/TypeScript |
| `docker-checks` | Verify Docker image builds |
| `security-checks` | Dependency vulnerability audit |

### 2. Docker Publish (`docker-publish.yml`)

**Triggers:**
- `workflow_run` from CI (for `develop` branch only)
- `workflow_call` from release.yml (for `main` releases)

### 3. Release (`release.yml`)

**Trigger:** `workflow_run` from CI (for `main` branch only)

Uses [semantic-release](https://semantic-release.gitbook.io/) to:
1. Analyze commit messages since last release
2. Determine next version number
3. Generate/update CHANGELOG.md
4. Create Git tag and GitHub Release
5. Trigger Docker build with version tags

### 4. PR Checks (`pr-checks.yml`)

**Trigger:** Pull request opened/updated

Optimized checks that only run on changed files:
- API lint only if `api/**` changed
- Web lint only if `web/**` changed

### 5. Code Quality (`code-quality.yml`)

**Trigger:** Pull request

- Commit message linting (Conventional Commits)
- TODO/FIXME detection
- Code complexity analysis
- Large file detection

---

## Docker Image Tags

Images are published to GitHub Container Registry (GHCR):

```
ghcr.io/ideaportriga/magnet-ai
```

### Stable Releases (from main)

| Tag | Example | Description |
|-----|---------|-------------|
| `latest` | `latest` | Latest stable release |
| `X.Y.Z` | `1.2.0` | Specific version |
| `vX.Y.Z` | `v1.2.0` | Specific version with prefix |

### Prerelease Versions (from develop)

| Tag | Example | Description |
|-----|---------|-------------|
| `dev` | `dev` | Latest development build |
| `X.Y.Z-dev.N` | `1.3.0-dev.1` | Specific dev version |
| `vX.Y.Z-dev.N` | `v1.3.0-dev.1` | Specific dev version with prefix |

### Version Progression Example

```
develop: feat: add feature A
         → v1.3.0-dev.1 (Docker: dev, 1.3.0-dev.1)
         
develop: fix: bug fix
         → v1.3.0-dev.2 (Docker: dev, 1.3.0-dev.2)

main:    merge develop → main
         → v1.3.0 (Docker: latest, 1.3.0)

develop: feat: new feature B  
         → v1.4.0-dev.1 (Docker: dev, 1.4.0-dev.1)
```

### Usage Examples

```bash
# Always use latest stable
docker pull ghcr.io/ideaportriga/magnet-ai:latest

# Pin to specific stable version
docker pull ghcr.io/ideaportriga/magnet-ai:1.2.0

# Use latest development version
docker pull ghcr.io/ideaportriga/magnet-ai:dev

# Pin to specific dev version
docker pull ghcr.io/ideaportriga/magnet-ai:1.3.0-dev.2
```

---

## Release Process

### Automatic Release (Recommended)

1. Merge PR with conventional commits to `develop`
2. When ready for release, create PR from `develop` → `main`
3. After merge, CI runs automatically
4. If releasable commits exist, semantic-release creates a new version
5. Docker image is built and pushed with appropriate tags

### Manual Release (Emergency)

Use the workflow dispatch feature:

1. Go to **Actions** → **Release - Semantic Versioning**
2. Click **Run workflow**
3. Optionally enable "Dry run mode" to preview without releasing

### Hotfix Process

For critical production fixes:

1. Create branch from `main`: `hotfix/critical-bug`
2. Fix the issue
3. Create PR directly to `main`
4. After merge, version will be bumped as patch
5. Back-merge `main` → `develop` to sync

---

## Workflow Dependencies

```
┌──────────┐     workflow_run      ┌──────────────────┐
│  ci.yml  │ ──────────────────►   │ docker-publish   │  (develop only)
│          │     (develop)         │                  │
└──────────┘                       └──────────────────┘

┌──────────┐     workflow_run      ┌──────────────┐     workflow_call     ┌──────────────────┐
│  ci.yml  │ ──────────────────►   │  release.yml │ ──────────────────►   │ docker-publish   │
│          │     (main)            │              │    (if version)       │                  │
└──────────┘                       └──────────────┘                       └──────────────────┘
```

---

## Key Guarantees

✅ **Lint before Docker** — Docker builds only trigger after successful CI  
✅ **No duplicates** — Each branch has a single path to Docker build  
✅ **Versioned releases** — Every release gets unique version tags  
✅ **`latest` = last release** — Not just the latest commit on main  
✅ **Atomic releases** — Git tag, GitHub Release, and Docker image created together

---

## Troubleshooting

### Release not created after merge to main

Check if your commits follow Conventional Commits format. Only these types trigger releases:
- `feat:` (minor)
- `fix:`, `perf:`, `refactor:`, `revert:` (patch)
- `feat!:` or `BREAKING CHANGE:` (major)

### Docker image not updated

1. Check if CI passed (Actions → CI - Linting and Tests)
2. For `main`: verify semantic-release created a version
3. For `develop`: verify workflow_run triggered docker-publish

### View release history

```bash
git tag --sort=-v:refname | head -10
```

Or check [GitHub Releases](../../releases) page.
