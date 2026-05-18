# Sign-in providers

Magnet exposes a single login screen that picks up whichever
providers are configured at boot. The set of enabled providers is
controlled by the `AUTH_PROVIDERS` environment variable.

## Default behaviour

```bash
AUTH_PROVIDERS=
```

When empty (the default), Magnet enables:

- `local` — implicitly always on.
- Any **built-in provider** (Microsoft, Google, GitHub) that has
  client credentials set.

Generic OIDC providers discovered via `OIDC_{NAME}_*` env vars
require **explicit inclusion** in `AUTH_PROVIDERS`.

## Forcing a subset

To restrict logins (for example to SSO only, locking out
email/password):

```bash
AUTH_PROVIDERS=microsoft
```

Multiple providers are comma-separated:

```bash
AUTH_PROVIDERS=local,microsoft,keycloak
```

::: warning
Removing `local` from `AUTH_PROVIDERS` immediately locks out every
account that doesn't have a linked SSO identity. Always leave a
break-glass path until the SSO flow is verified end-to-end.
:::

## Local email / password

`local` is the implicit default. Users register via the **Signup**
page (or the `POST /api/v2/auth/signup` endpoint). Behaviour
controlled by:

| Variable | Default | Effect |
|---|---|---|
| `REQUIRE_EMAIL_VERIFICATION` | `false` | When `true`, refuse local logins until the user has clicked the link in their verification email. SSO users are exempt. |
| `ACCESS_TOKEN_EXPIRATION_MINUTES` | `15` | Lifetime of the access JWT. |
| `REFRESH_TOKEN_EXPIRATION_DAYS` | `7` | Lifetime of refresh tokens. |

Passwords are hashed with **Argon2id**. Reset flow uses a
single-use token mailed to the user; tokens carry the requesting
IP and are invalidated after first use.

## Microsoft Entra ID (Azure AD)

```bash
AUTH_PROVIDERS=microsoft
MICROSOFT_ENTRA_ID_TENANT_ID=<azure-tenant-uuid>
MICROSOFT_ENTRA_ID_CLIENT_ID=<application-id>
MICROSOFT_ENTRA_ID_CLIENT_SECRET=<application-secret>
MICROSOFT_ENTRA_ID_REDIRECT_URI=https://<your-host>/api/v2/auth/oauth/microsoft/callback
```

The redirect URI must be added to your Entra App's
**Authentication → Web → Redirect URIs**. Magnet treats the email
returned by `id_token` as the canonical identifier — repeat
logins find the same user record.

## Google

```bash
AUTH_PROVIDERS=google
GOOGLE_OAUTH2_CLIENT_ID=<client-id>
GOOGLE_OAUTH2_CLIENT_SECRET=<client-secret>
OAUTH2_REDIRECT_BASE_URL=https://<your-host>
```

Register the same `OAUTH2_REDIRECT_BASE_URL` + `/api/v2/auth/oauth/google/callback`
in your Google Cloud OAuth client.

## GitHub

```bash
AUTH_PROVIDERS=github
GITHUB_OAUTH2_CLIENT_ID=<client-id>
GITHUB_OAUTH2_CLIENT_SECRET=<client-secret>
OAUTH2_REDIRECT_BASE_URL=https://<your-host>
```

GitHub's email visibility setting affects which address is
returned. Users with only private emails will receive a
`noreply@users.github.com` placeholder unless they expose at
least one verified address.

## Generic OIDC provider

To wire any OIDC-conformant provider (Keycloak, Okta, Auth0,
Cognito, …), declare it with a name of your choice:

```bash
AUTH_PROVIDERS=local,keycloak
OIDC_KEYCLOAK_DISCOVERY_URL=https://kc.example.com/realms/magnet/.well-known/openid-configuration
OIDC_KEYCLOAK_CLIENT_ID=magnet-admin
OIDC_KEYCLOAK_CLIENT_SECRET=<secret>
```

The provider name (`keycloak` here) becomes the URL path segment
and the button label on the login page.

## First-time SSO sign-ins

When a brand-new SSO user logs in, Magnet creates a user record
with their email, marks it `is_verified=true`, and assigns **no
roles**. They will see only their own profile until an admin
opens **System → Users** and grants them the appropriate role.
See [Managing users](../access/users).

## Local provider in production

If you keep `local` enabled in production, also:

- Set `AUTH_COOKIE_SECURE=true` (the default) so cookies are
  transmitted only over HTTPS.
- Set `REQUIRE_EMAIL_VERIFICATION=true` to block self-registered
  drivebys.
- Limit signups by gating `POST /api/v2/auth/signup` upstream
  (reverse proxy, firewall) until a future invite-only mode
  lands.
