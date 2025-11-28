# Git Workflow Guide

**For a 5-person team | Public GitHub Repository | Active Development + Releases + Experiments**

---

## 1. Long-lived branches
| Branch     | Purpose                                         | Who can push directly    |
|------------|-------------------------------------------------|--------------------------|
| `main`     | Only production-ready code                      | Owner / tech lead only   |
| `develop`  | Integration branch – all new features go here   | Only via Pull Request    |

## 2. Short-lived branches
| Prefix         | Example                        | When to create                             |
|----------------|--------------------------------|--------------------------------------------|
| `feature/`     | `feature/user-avatars`         | Regular new functionality                  |
| `hotfix/`      | `hotfix/payment-bug`           | Urgent production fix                      |
| `release/`     | `release/2.1.0`                | Preparing a new release                    |
| `experiment/`  | `experiment/ai-assistant`      | Experiments (see how to hide below)        |

## 3. Daily workflow
**For Core Team:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-task-name
# work → commit often
git push -u origin feature/your-task-name
```

**For External Contributors:**
1. Fork the repository.
2. Clone your fork.
3. Create a branch from `develop`.
4. Push to your fork.

**Creating a Pull Request:**
1. Open Pull Request → `develop`.
2. Link issue in description: `Fixes #123`.
3. Wait for ≥1 approval + CI green.
4. Merge (Squash and merge recommended).

## 4. Release Process & Docker Build
**Goal:** Publish a production-ready Docker container to the registry (GHCR/DockerHub).

1. **Prepare Release:**
   ```bash
   git checkout develop
   git checkout -b release/2.1.0
   # bump versions (package.json, pyproject.toml)
   # update CHANGELOG.md
   git commit -m "Bump version to 2.1.0"
   git push origin release/2.1.0
   ```
   *Open PR to `main`. After approval and merge:*

2. **Create Tag (Build Trigger):**
   ```bash
   git checkout main
   git pull origin main
   git tag -a v2.1.0 -m "Release 2.1.0"
   git push origin v2.1.0
   ```

3. **Automated Build (CI/CD):**
   GitHub Actions detects the `v*` tag push, as well as pushes to `main` and `develop`:
   *   Builds the Docker image.
   *   Tags it as `latest` (for main), `dev` (for develop), and `v2.1.0` (for tags).
   *   Pushes to Container Registry.
   *   Creates a GitHub Release (for main only).

4. **Cleanup:**
   Merge `release/2.1.0` (or `main`) back into `develop` to sync versions.

## 5. Hotfixes
Same as release but from `main` → create `hotfix/...` → merge to `main` + tag patch version → merge back to `develop`.

## 6. Automation
GitHub Actions:
- Tests on every PR and push to `develop`/`main` (`ci.yml`)
- Build & push Docker image on push to `main`, `develop`, or `v*` tag (`docker-publish.yml`)
- Create Release on push to `main` (`release.yml`)

## 7. Artifact storage
- Docker images → GitHub Container Registry
- Packages → GitHub Packages
- Binaries → GitHub Releases
