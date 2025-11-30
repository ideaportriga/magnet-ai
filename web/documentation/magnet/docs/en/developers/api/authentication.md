# Authentication

Magnet AI supports two primary methods for authentication: **OAuth2/OIDC** for user sessions (Web UI) and **API Keys** for programmatic access.

## Authentication Methods

### 1. API Key Authentication (Programmatic Access)

For scripts, external integrations, and development, use the API Key method.

**Header:** `x-api-key`

#### Example Request

**cURL:**

```bash
curl -H "x-api-key: YOUR_API_KEY" \
  http://localhost:5000/api/agents
```

**Python:**

```python
import requests

headers = {
    'x-api-key': 'YOUR_API_KEY',
    'Content-Type': 'application/json'
}

response = requests.get(
    'http://localhost:5000/api/agents',
    headers=headers
)
```

### 2. OAuth2 / OIDC (User Sessions)

The Web UI uses OAuth2 (OpenID Connect) for user authentication. This is handled via browser cookies.

**Supported Providers:**

- Microsoft Entra ID (Azure AD)
- Oracle Identity Cloud Service

**Flow:**

1. User visits `/api/auth/login`
2. Redirects to Identity Provider
3. Returns to `/api/auth/callback`
4. Sets `token` and `refresh_token` cookies

## Authorization

Magnet AI implements Role-Based Access Control (RBAC).

### Roles

- **Admin**: Full system access.
- **User**: Standard access.

### Guards

Some endpoints are protected by role guards:

```python
from guards.role import UserRole, create_role_guard

@get("/admin/settings", guards=[create_role_guard(UserRole.ADMIN)])
def admin_settings() -> dict:
    ...
```

## Environment Configuration

Authentication is configured via environment variables in `api/src/config/auth.py`.

### General

- `AUTH_PROVIDER`: `MICROSOFT` or `ORACLE`

### Microsoft Entra ID

- `MICROSOFT_ENTRA_ID_TENANT_ID`
- `MICROSOFT_ENTRA_ID_CLIENT_ID`
- `MICROSOFT_ENTRA_ID_CLIENT_SECRET`
- `MICROSOFT_ENTRA_ID_REDIRECT_URI`

### Oracle

- `ORACLE_AUTH_TENANT_URL`
- `ORACLE_AUTH_CLIENT_ID`
- `ORACLE_AUTH_CLIENT_SECRET`
- `ORACLE_AUTH_REDIRECT_URL`

## Security Best Practices

1. **Keep API Keys Secret**: Never commit API keys to version control.
2. **Use HTTPS**: Always use HTTPS in production to protect headers and cookies.
3. **Rotate Keys**: Regularly rotate API keys and secrets.
