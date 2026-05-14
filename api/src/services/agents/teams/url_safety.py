"""URL safety helpers for admin-provided media URLs.

The note-taker admin UI accepts a free-form ``source_url`` for preview
jobs. The worker fetches that URL inside the cluster, so an unfiltered
URL is a textbook SSRF vector:

* internal services on the docker network (``redis://``, ``http://api``),
* cloud metadata endpoints (``169.254.169.254``),
* link-local / RFC1918 ranges that point at the operator's home LAN
  via misconfigured NAT.

This module is the single boundary check. We restrict to https (Graph
recordings are always https), resolve the hostname, and reject the
request if the resolved address falls inside any of the well-known
non-public ranges. Caller gets a :class:`UnsafeSourceURLError` and the
controller returns 400.

See docs/NOTE_TAKER_RELIABILITY_PLAN.md § P2-5.
"""

from __future__ import annotations

import ipaddress
import socket
from logging import getLogger
from urllib.parse import urlparse

logger = getLogger(__name__)


class UnsafeSourceURLError(ValueError):
    """Raised when a user-supplied URL fails the SSRF safety check."""


_ALLOWED_SCHEMES = frozenset({"https"})


def _addr_is_safe(addr: str) -> bool:
    """Return True iff ``addr`` is a globally-routable IP we'd hit on the public internet."""
    try:
        ip = ipaddress.ip_address(addr)
    except ValueError:
        return False
    if ip.is_private:
        return False
    if ip.is_loopback:
        return False
    if ip.is_link_local:
        return False
    if ip.is_reserved:
        return False
    if ip.is_multicast:
        return False
    if ip.is_unspecified:
        return False
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        # 6→4 mapped addresses inherit the embedded IPv4's class.
        return _addr_is_safe(str(ip.ipv4_mapped))
    return True


def _resolve_all(hostname: str) -> list[str]:
    """Resolve all addresses for ``hostname`` (IPv4 + IPv6). Empty list on failure."""
    try:
        infos = socket.getaddrinfo(hostname, None, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return []
    return list({info[4][0] for info in infos})


def check_source_url(url: str) -> None:
    """Validate that ``url`` is safe to fetch from a worker process.

    Raises :class:`UnsafeSourceURLError` on any of:

    * empty / un-parseable URL,
    * scheme other than ``https``,
    * missing host,
    * any DNS-resolved address that falls in a private/loopback/
      link-local/reserved/multicast/unspecified range — even one
      bad answer poisons the result (DNS rebinding defence).

    On success this returns ``None`` and the caller proceeds to fetch.
    Note that DNS rebinding is still possible between this check and
    the actual fetch — callers that need stronger guarantees should
    bind the resolved IP into the fetch directly.
    """
    if not url or not isinstance(url, str):
        raise UnsafeSourceURLError("URL is empty")

    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES:
        raise UnsafeSourceURLError(
            f"URL scheme {parsed.scheme!r} not allowed (https only)"
        )
    if not parsed.hostname:
        raise UnsafeSourceURLError("URL has no hostname")

    # Direct-IP URLs skip DNS but still need range check.
    try:
        ipaddress.ip_address(parsed.hostname)
        addresses: list[str] = [parsed.hostname]
    except ValueError:
        addresses = _resolve_all(parsed.hostname)
        if not addresses:
            raise UnsafeSourceURLError(
                f"could not resolve hostname {parsed.hostname!r}"
            )

    for addr in addresses:
        if not _addr_is_safe(addr):
            raise UnsafeSourceURLError(
                f"hostname {parsed.hostname!r} resolves to non-public address {addr}"
            )
