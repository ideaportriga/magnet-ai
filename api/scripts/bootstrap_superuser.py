#!/usr/bin/env python3
"""Create or promote a superuser for a fresh deployment.

Reads credentials from environment variables and is safe to re-run — the
underlying service is idempotent.

Required env:
    BOOTSTRAP_SUPERUSER_EMAIL
    BOOTSTRAP_SUPERUSER_PASSWORD

Optional env:
    BOOTSTRAP_SUPERUSER_NAME            display name
    BOOTSTRAP_SUPERUSER_RESET_PASSWORD  if "true", overwrite the password of
                                        an existing user (default: false)
    BOOTSTRAP_ALLOW_PRODUCTION          must be "true" to allow running with
                                        ENV=production (default: refuse)

Exit codes:
    0  success (created, updated, or no-op)
    2  missing/invalid configuration
    3  refused — production guard tripped
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

# Add `src` to import path BEFORE importing app modules.
SRC_PATH = Path(__file__).resolve().parent.parent / "src"
sys.path.insert(0, str(SRC_PATH))

from config.config import load_env  # noqa: E402

load_env()

# Now safe to import settings/services.
from core.config.app import alchemy  # noqa: E402
from services.users.bootstrap import bootstrap_superuser  # noqa: E402


_WEAK_PASSWORDS = {
    "password",
    "password123",
    "admin",
    "admin123",
    "magnet",
    "magnetai",
    "12345678",
    "qwerty123",
}


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def _fail(message: str, code: int = 2) -> None:
    print(f"❌ {message}", file=sys.stderr)
    sys.exit(code)


async def _run() -> int:
    email = (os.environ.get("BOOTSTRAP_SUPERUSER_EMAIL") or "").strip()
    password = os.environ.get("BOOTSTRAP_SUPERUSER_PASSWORD") or ""
    name = (os.environ.get("BOOTSTRAP_SUPERUSER_NAME") or "").strip() or None
    reset_password = _truthy(os.environ.get("BOOTSTRAP_SUPERUSER_RESET_PASSWORD"))

    if not email:
        _fail(
            "BOOTSTRAP_SUPERUSER_EMAIL is required. "
            "Set it in .env or pass it on the command line."
        )
    if "@" not in email:
        _fail(f"BOOTSTRAP_SUPERUSER_EMAIL does not look like an email: {email!r}")
    if not password:
        _fail(
            "BOOTSTRAP_SUPERUSER_PASSWORD is required. "
            "Pick a strong password and set it in .env."
        )
    if len(password) < 12:
        _fail("BOOTSTRAP_SUPERUSER_PASSWORD must be at least 12 characters long.")
    if password.lower() in _WEAK_PASSWORDS:
        _fail(
            "BOOTSTRAP_SUPERUSER_PASSWORD is on the well-known-weak list. "
            "Pick a stronger password."
        )

    env_name = (os.environ.get("ENV") or "").strip().lower()
    if env_name == "production" and not _truthy(
        os.environ.get("BOOTSTRAP_ALLOW_PRODUCTION")
    ):
        _fail(
            "Refusing to bootstrap a superuser in production without "
            "BOOTSTRAP_ALLOW_PRODUCTION=true.",
            code=3,
        )

    async with alchemy.get_session() as session:
        result = await bootstrap_superuser(
            session,
            email=email,
            password=password,
            name=name,
            reset_password=reset_password,
        )
        await session.commit()

    if result.created:
        print(f"✅ Created superuser {result.email} (id={result.user_id})")
    elif result.updated:
        print(f"✅ Promoted existing user {result.email} (id={result.user_id})")
    else:
        print(f"✅ No-op — {result.email} is already a superuser")

    if not result.role_assigned and not result.created:
        # Already had the role; just informational.
        pass
    return 0


def main() -> None:
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()
