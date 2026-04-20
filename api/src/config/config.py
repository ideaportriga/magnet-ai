"""Project-root .env loader with fail-fast validation.

Single source of truth for environment loading. Called from app.py at import
time, BEFORE anything reads `os.environ` or initialises cached settings.

Resolution rules (BACKEND_FIXES_ROADMAP.md §A.3):

1. Project root is resolved relative to this file's path — **not** cwd — so it
   doesn't matter whether the server is launched from `/` or from `api/`.
2. Base layer: `<root>/.env` (always loaded if present).
3. Override layer: `<root>/.env.{ENV}` (loaded on top of base when `ENV` is set
   and the file exists — e.g. `.env.production`).
4. Required vars (SECRET_ENCRYPTION_KEY unconditionally; DATABASE_URL and
   SECRET_KEY additionally in production) must be present after loading,
   otherwise the process exits 1. An insecure shipped default for
   SECRET_ENCRYPTION_KEY is also rejected.

Notes:
- `api/.env` is intentionally NOT consulted. Migrate any local overrides
  to the project-root `.env` (or `.env.local`, which `.env.{ENV}` mechanism
  supports via `ENV=local`).
- Pydantic `BaseSettings` loaders elsewhere read from `os.environ`, which
  is already populated by the time they run.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import structlog
from dotenv import load_dotenv

logger = structlog.get_logger(__name__)


# /Users/.../magnet-ai/api/src/config/config.py → parents[3] = project root.
# Computed once at import; doesn't depend on cwd.
PROJECT_ROOT: Path = Path(__file__).resolve().parents[3]


def _load_file(path: Path, *, override: bool) -> bool:
    """load_dotenv wrapper that returns whether the file existed."""
    if not path.is_file():
        return False
    load_dotenv(dotenv_path=path, override=override)
    logger.info("Loaded env file", path=str(path), override=override)
    return True


def load_env() -> None:
    """Populate os.environ from `<root>/.env` (+ `<root>/.env.{ENV}` override) and validate."""
    base_loaded = _load_file(PROJECT_ROOT / ".env", override=False)

    env_name = os.environ.get("ENV", "").strip()
    override_loaded = False
    if env_name:
        override_loaded = _load_file(PROJECT_ROOT / f".env.{env_name}", override=True)

    if not base_loaded and not override_loaded:
        logger.warning(
            "No .env file found under project root",
            project_root=str(PROJECT_ROOT),
        )

    _validate_required(env_name.lower())


def _validate_required(env_name_lower: str) -> None:
    is_production = env_name_lower == "production"

    required = ["SECRET_ENCRYPTION_KEY"]
    if is_production:
        required += ["DATABASE_URL", "SECRET_KEY"]

    missing = [var for var in required if not os.environ.get(var)]
    if missing:
        logger.error(
            "Required environment variables are not defined",
            missing=missing,
        )
        sys.exit(1)

    # Reject the legacy shipped default for SECRET_ENCRYPTION_KEY in production.
    # Dev databases may still be encrypted with it from the pre-A.3 era, so we
    # let it through locally with a loud warning instead of blocking startup.
    # See BACKEND_FIXES_ROADMAP.md §A.3.
    insecure_defaults = {
        "SECRET_ENCRYPTION_KEY": "my-secret-key-tsmh5r",
    }
    for var, insecure_value in insecure_defaults.items():
        if os.environ.get(var) != insecure_value:
            continue
        if is_production:
            logger.error(
                "%s is set to the insecure shipped default. Set a strong value.",
                var,
            )
            sys.exit(1)
        logger.warning(
            "%s is the legacy shipped default. Acceptable for dev to read "
            "pre-existing encrypted rows; rotate before going to production.",
            var,
        )
