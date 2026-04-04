"""
Password hashing and verification using Argon2 via pwdlib.

Argon2 is intentionally CPU-intensive (~100-300ms per operation).
Both functions offer sync and async variants:
- ``hash_password`` / ``verify_password`` — sync (for use in threads, tests)
- ``hash_password_async`` / ``verify_password_async`` — non-blocking
  (runs the CPU work in a thread so the event loop is not stalled)
"""

from __future__ import annotations

import asyncio

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2 (sync, blocks the caller)."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash (sync, blocks the caller)."""
    return _password_hash.verify(plain_password, hashed_password)


async def hash_password_async(password: str) -> str:
    """Hash a plaintext password with Argon2 without blocking the event loop."""
    return await asyncio.to_thread(_password_hash.hash, password)


async def verify_password_async(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against an Argon2 hash without blocking the event loop."""
    return await asyncio.to_thread(
        _password_hash.verify, plain_password, hashed_password
    )
