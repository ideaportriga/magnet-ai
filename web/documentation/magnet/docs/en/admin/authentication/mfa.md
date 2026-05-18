# Multi-factor authentication

Magnet supports **TOTP**-based multi-factor authentication (the
same flavour used by Google Authenticator, 1Password, Authy, etc.).
MFA is opt-in per user and lives under **Profile → Security**.

## Enabling MFA on your account

1. Sign in and open **Profile**.
2. Switch to the **Security** tab.
3. Click **Enable two-factor authentication**.
4. Scan the displayed QR code with your authenticator app, or copy
   the secret manually.
5. Confirm by entering the 6-digit code your app generates.
6. Save the **backup codes** shown afterwards — each is one-shot
   and they're the only way back in if you lose access to your
   authenticator.

After enabling, every login asks for the 6-digit code in addition
to your password. SSO logins are not affected — they inherit the
trust level of the upstream provider.

## Backup codes

Each user receives **eight** single-use codes when MFA is first
enabled. Use one when prompted in place of the 6-digit TOTP code.
A user can:

- **Regenerate** the codes from **Profile → Security** at any
  time — this invalidates the previous set.
- **See** how many are still unused (consumed codes are not
  re-displayed).

Treat them like passwords. Store in your password manager, not
in a screenshot folder.

## Storage and encryption

TOTP secrets and the hashed backup codes live on the user record.
The TOTP shared secret is encrypted at rest using the application
`SECRET_ENCRYPTION_KEY` — losing this key permanently breaks MFA
for every user that has enabled it. Rotation requires a coordinated
migration; do not change `SECRET_ENCRYPTION_KEY` in place.

## Disabling MFA for a user

The user themselves can disable MFA from **Profile → Security**
after entering their password. Admins cannot disable another user's
MFA through the UI — the safer path when a user is locked out is:

1. Confirm their identity through an out-of-band channel.
2. Use a backup code if they have one.
3. As a last resort, a platform operator with database access can
   clear `mfa_enabled`, `totp_secret_encrypted`, and the backup
   code hashes on the user row.

Each option leaves an audit trail: backup-code use is recorded as
a normal `login.success` with `auth_method=mfa_recovery`; manual
clears via SQL are out of scope of the application audit log.

## Enforcing MFA tenant-wide

A flag to **require** MFA for all users in a tenant is on the
roadmap. Until then, the policy is operational — set expectations
in onboarding and audit non-compliant users via:

```http
GET /api/admin/users
```

The response includes `is_two_factor_enabled` for every user.

## API keys and MFA

API keys are unaffected by MFA — they bypass the user login flow
entirely and authenticate via their scope list. If you need
strong-credential protection for an automation, generate a key
with the minimum required scopes and rotate frequently. See
[API keys](./api-keys).
