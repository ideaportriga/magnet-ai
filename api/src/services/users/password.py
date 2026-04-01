"""
Password hashing and verification using Argon2 via pwdlib.

All operations are CPU-bound and should be called from async context
(pwdlib handles this internally).
"""

from __future__ import annotations

from pwdlib import PasswordHash
from pwdlib.hashers.argon2 import Argon2Hasher

_password_hash = PasswordHash((Argon2Hasher(),))


def hash_password(password: str) -> str:
    """Hash a plaintext password with Argon2."""
    return _password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against an Argon2 hash."""
    return _password_hash.verify(plain_password, hashed_password)
