# Sessions and tokens

Magnet uses a pair of tokens for every authenticated session:

| Token | Lifetime (default) | Carrier | Stored where |
|---|---|---|---|
| **Access** | 15 min | `Authorization` header **or** `magnet_access` cookie | Not persisted server-side. Validated by signature + expiry. |
| **Refresh** | 7 days | `magnet_refresh` cookie | Hashed on the `auth_refresh_token` table; rotated on every use. |

Lifetimes are configurable via
`ACCESS_TOKEN_EXPIRATION_MINUTES` and
`REFRESH_TOKEN_EXPIRATION_DAYS`.

## Refresh-token rotation

When the admin UI receives a 401 on a request, it transparently
hits `POST /api/v2/auth/refresh`. The server:

1. Verifies the presented refresh token hash exists and isn't
   revoked.
2. Marks it as **used** and stamps a brand-new refresh token with
   the same `family_id`.
3. Returns a fresh access token + sets the new refresh cookie.

If the **same** refresh token is presented twice (e.g. an
attacker replayed a captured cookie), Magnet revokes the entire
**token family** — every refresh ever derived from that family
is invalidated and the legitimate user is forced to log in
again. This is the standard family-based reuse detection
protocol.

A small grace window (`REFRESH_TOKEN_REUSE_GRACE_SECONDS=5`)
absorbs benign duplicate refreshes from clients with multiple
tabs sharing one cookie — within the grace window, replays don't
trigger the family kill switch.

## Active sessions list

Users can see and manage their own sessions from
**Profile → Security → Sessions**. The list shows:

- The user-agent (browser / device) at session creation.
- The IP that initiated the session.
- The created-at timestamp.
- The last-seen timestamp.

Each row has a **Revoke** button. **Revoke all other sessions**
at the top kills every session except the current browser tab.

::: tip
"Revoke" deletes the refresh-token row immediately and lets the
access token expire naturally. Within the access-token TTL
(default 15 min) the user can still call the API; after that
they will be redirected to login. Set
`ACCESS_TOKEN_EXPIRATION_MINUTES` lower if your security model
requires tighter revocation.
:::

## Logging out

The **Logout** button at the bottom of the sidebar:

1. Calls `POST /api/v2/auth/logout`, which deletes the active
   refresh row and clears both cookies.
2. Writes a `logout` entry to the [access log](../access/access-log).

If the user is logged in through SSO, Magnet's logout does not
sign them out of the upstream IdP — they remain signed in at
e.g. Microsoft / Google and will be silently re-authenticated
on next login.

## Cookie domain and `Secure`

Two settings control cookie behaviour for browser logins:

| Variable | Default | Effect |
|---|---|---|
| `AUTH_COOKIE_SECURE` | `true` | Send cookies only over HTTPS. Keep `true` outside local HTTP dev. |
| `AUTH_COOKIE_DOMAIN` | `""` | Optional `Domain=` attribute. Set when the admin UI and API live on different subdomains of the same parent. |

For multi-host deployments behind a reverse proxy, pin
`AUTH_COOKIE_DOMAIN=.your-domain.com` so the cookie is available
on both `admin.your-domain.com` and `api.your-domain.com`.

## Inspecting tokens

Both tokens are signed HS256 JWTs. The access token carries:

- `sub` — email
- `extras.user_id` — UUID
- `extras.is_superuser` — boolean
- `extras.is_verified` — boolean
- `extras.auth_method` — `password` / `mfa` / `oauth` / `api_key`
- `extras.roles` — list of role slugs at issue time

A user with an in-flight access token whose **role grants
change** keeps their old permission set until the token expires
(up to 15 min by default). The permission cache on the API is
invalidated immediately, so the next refresh picks up the new
state — but the access token itself is not invalidated on role
change to avoid synchronous DB lookups on every request.

For zero-tolerance revocation, drop the access token TTL and rely
on refresh cycles to enforce the new permissions.
