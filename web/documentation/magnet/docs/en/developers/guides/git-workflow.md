# Git Workflow Guide

**For a 5-person team | Public GitHub Repository | Active Development + Releases + Experiments**

---

## 1. Long-lived branches

| Branch    | Purpose                                       | Who can push directly  |
| --------- | --------------------------------------------- | ---------------------- |
| `main`    | Only production-ready code                    | Owner / tech lead only |
| `develop` | Integration branch – all new features go here | Only via Pull Request  |

## 2. Short-lived branches

| Prefix        | Example                   | When to create                      |
| ------------- | ------------------------- | ----------------------------------- |
| `feature/`    | `feature/user-avatars`    | Regular new functionality           |
| `hotfix/`     | `hotfix/payment-bug`      | Urgent production fix               |
| `release/`    | `release/2.1.0`           | Preparing a new release             |
| `experiment/` | `experiment/ai-assistant` | Experiments (see how to hide below) |

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

## 4. Commit Messages

We follow the **Conventional Commits** specification. This allows us to automatically generate changelogs and determine semantic versioning.

**Format**: `<type>(<scope>): <description>`

**Types**:
- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Changes that do not affect the meaning of the code (white-space, formatting, etc)
- `refactor`: A code change that neither fixes a bug nor adds a feature
- `perf`: A code change that improves performance
- `test`: Adding missing tests or correcting existing tests
- `chore`: Changes to the build process or auxiliary tools and libraries such as documentation generation

**Examples**:
- `feat(api): add new endpoint for user profile`
- `fix(web): resolve issue with login button`
- `docs: update readme with setup instructions`

We use `commitlint` to enforce these rules. If your commit message does not follow the convention, the commit will be rejected.

## 5. Release Process & Docker Build

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

   _Open PR to `main`. After approval and merge:_

2. **Create Tag (Build Trigger):**

   ```bash
   git checkout main
   git pull origin main
   git tag -a v2.1.0 -m "Release 2.1.0"
   git push origin v2.1.0
   ```

3. **Automated Build (CI/CD):**
   GitHub Actions detects the `v*` tag push, as well as pushes to `main` and `develop`:
   - Builds the Docker image.
   - Tags it as `latest` (for main), `dev` (for develop), and `v2.1.0` (for tags).
   - Pushes to Container Registry.
   - Creates a GitHub Release (for main only).

4. **Cleanup:**
   Merge `release/2.1.0` (or `main`) back into `develop` to sync versions.

## 6. Hotfixes

Same as release but from `main` → create `hotfix/...` → merge to `main` + tag patch version → merge back to `develop`.

## 7. Automation

GitHub Actions:

- Tests on every PR and push to `develop`/`main` (`ci.yml`)
- Build & push Docker image on push to `main`, `develop`, or `v*` tag (`docker-publish.yml`)
- Create Release on push to `main` (`release.yml`)

## 8. Artifact storage

- Docker images → GitHub Container Registry
- Packages → GitHub Packages
- Binaries → GitHub Releases
