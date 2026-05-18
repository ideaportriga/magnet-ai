# Authentication

Magnet AI ships with a complete authentication stack rebuilt for
the alpha release. End users can sign in with:

- **Local email + password** (Argon2 hashing, optional email
  verification and TOTP MFA).
- **OAuth / OIDC** social providers — Microsoft Entra ID, Google,
  and GitHub are wired in out of the box; any other
  OIDC-conformant provider can be added with one set of env vars.
- **API keys** — long-lived tokens with their own scope list,
  used for backend-to-backend and CI integrations.

Server-issued **JWT access tokens** (HS256, 15 min default) are
paired with **refresh tokens** (7 days, rotated on every use with
family-based reuse detection). Sessions are tracked per-device so
you can revoke individual ones.

This section covers:

- [Sign-in providers](./providers) — choosing and configuring
  local, OAuth, and OIDC providers.
- [Multi-factor authentication](./mfa) — enabling TOTP and
  managing backup codes.
- [Sessions and tokens](./sessions) — how access / refresh
  tokens work and how to revoke them.
- [API keys](./api-keys) — managing programmatic access.

::: tip Where this fits
**Authentication** answers *who is the user?* — separate from
**[authorization](../access/overview)** which answers *what may
they do?*. Even with auth fully enabled, every API call still
runs through the RBAC layer before reaching application logic.
:::

## Enabling authentication

Authentication is gated by a single switch. In your `.env`:

```bash
AUTH_ENABLED=true
```

When `false` (the default in the example file), every request is
treated as anonymous and route guards are bypassed — useful for
purely local development but **never** for shared or production
deployments.

Once enabled, you must:

1. **Set a JWT secret**:

   ```bash
   SECRET_KEY=<a random 32-byte hex string>
   ```

   An empty `SECRET_KEY` disables local JWT auth.

2. **Pick at least one provider** via `AUTH_PROVIDERS`. The default
   empty value enables `local` plus any built-in provider that has
   credentials configured. See [Sign-in providers](./providers).

3. **Bootstrap a superuser** to log in for the first time. Either
   run `npm run bootstrap:superuser` once, or set
   `AUTO_CREATE_SUPERUSER=true` so the API does it on startup.
   `BOOTSTRAP_SUPERUSER_EMAIL` and `BOOTSTRAP_SUPERUSER_PASSWORD`
   control the credentials. See
   [Getting started](../../developers/setup/getting-started).

## Cookies vs Bearer tokens

The admin UI uses **httpOnly cookies** for access and refresh
tokens — they cannot be read by JavaScript and the dev cookie
domain is set automatically. Programmatic clients (curl, Postman,
backend services) attach the access token as a
`Authorization: Bearer …` header instead.

Both flows hit the same endpoints under `/api/v2/auth`. The cookie
flow simply lets the browser carry the credentials transparently.

## Audit trail

Every successful login, failed login, and logout is written to the
[access log](../access/access-log) with action codes
`login.success`, `login.failure`, and `logout`. The payload
includes the auth method (`password`, `oauth`, `api_key`) and the
provider name for SSO logins; the actor on a failed login is the
**attempted** email, not a resolved user ID.
