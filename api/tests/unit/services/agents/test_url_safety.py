"""SSRF guard for admin-supplied source URLs.

Pins the contract from docs/NOTE_TAKER_RELIABILITY_PLAN.md § P2-5:
worker fetches public https URLs only — internal services, cloud
metadata, and private ranges are rejected at the controller boundary.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from services.agents.teams.url_safety import (
    UnsafeSourceURLError,
    check_source_url,
)


def _resolves_to(*addresses: str):
    """Return a patcher that makes socket.getaddrinfo yield the given addresses."""
    return patch(
        "services.agents.teams.url_safety.socket.getaddrinfo",
        return_value=[(0, 0, 0, "", (addr, 0)) for addr in addresses],
    )


def test_rejects_empty():
    with pytest.raises(UnsafeSourceURLError):
        check_source_url("")


def test_rejects_http_scheme():
    with pytest.raises(UnsafeSourceURLError):
        check_source_url("http://example.com/audio.mp3")


@pytest.mark.parametrize(
    "url",
    [
        "ftp://example.com/x.mp3",
        "file:///etc/passwd",
        "gopher://example.com/",
        "data:audio/mp3;base64,aGVsbG8=",
    ],
)
def test_rejects_non_https_schemes(url):
    with pytest.raises(UnsafeSourceURLError):
        check_source_url(url)


def test_rejects_missing_host():
    with pytest.raises(UnsafeSourceURLError):
        check_source_url("https:///path")


@pytest.mark.parametrize(
    "addr",
    [
        "127.0.0.1",  # loopback
        "10.0.0.5",  # RFC1918
        "192.168.1.1",  # RFC1918
        "172.16.0.1",  # RFC1918
        "169.254.169.254",  # link-local (AWS metadata)
        "0.0.0.0",  # unspecified
        "::1",  # IPv6 loopback
        "fe80::1",  # IPv6 link-local
        "fc00::1",  # IPv6 unique-local
    ],
)
def test_rejects_private_resolved_address(addr):
    with _resolves_to(addr):
        with pytest.raises(UnsafeSourceURLError):
            check_source_url("https://internal.example.com/audio.mp3")


def test_rejects_direct_private_ip_url():
    with pytest.raises(UnsafeSourceURLError):
        check_source_url("https://192.168.1.10/audio.mp3")


def test_rejects_direct_metadata_ip():
    with pytest.raises(UnsafeSourceURLError):
        check_source_url("https://169.254.169.254/latest/meta-data/")


def test_rejects_when_any_resolved_address_is_private():
    """DNS rebinding defence: a single private answer poisons the result."""
    with _resolves_to("8.8.8.8", "10.0.0.5"):
        with pytest.raises(UnsafeSourceURLError):
            check_source_url("https://attacker.example.com/audio.mp3")


def test_rejects_unresolvable_host():
    import socket

    with patch(
        "services.agents.teams.url_safety.socket.getaddrinfo",
        side_effect=socket.gaierror("no such host"),
    ):
        with pytest.raises(UnsafeSourceURLError):
            check_source_url("https://no-such-host.example/audio.mp3")


def test_accepts_public_ipv4():
    with _resolves_to("93.184.216.34"):  # example.com
        check_source_url("https://example.com/audio.mp3")


def test_accepts_public_ipv6():
    with _resolves_to("2606:2800:220:1:248:1893:25c8:1946"):
        check_source_url("https://example.com/audio.mp3")
