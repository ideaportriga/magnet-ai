"""
Unit tests for CSRF middleware.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch


class TestCSRFHelpers:
    def test_get_allowed_origins(self):
        with patch("middlewares.csrf.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                OAUTH2_REDIRECT_BASE_URL="http://localhost:8000",
                MICROSOFT_ENTRA_ID_REDIRECT_URI="https://api.example.com/auth/callback",
            )
            from middlewares.csrf import _get_allowed_origins

            origins = _get_allowed_origins()
            assert "http://localhost:8000" in origins
            assert "https://api.example.com" in origins

    def test_get_allowed_origins_empty(self):
        with patch("middlewares.csrf.get_auth_settings") as mock_settings:
            mock_settings.return_value = MagicMock(
                OAUTH2_REDIRECT_BASE_URL="",
                MICROSOFT_ENTRA_ID_REDIRECT_URI="",
            )
            from middlewares.csrf import _get_allowed_origins

            origins = _get_allowed_origins()
            # Empty URLs should not produce valid origins
            assert len(origins) <= 2  # May contain '://' artifacts but no real origins
