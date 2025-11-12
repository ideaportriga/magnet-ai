# Authentication

Magnet AI uses token-based authentication to secure API access. This guide explains how to authenticate and authorize API requests.

## Authentication Methods

### 1. API Token Authentication

The primary authentication method uses bearer tokens in the `Authorization` header.

#### Obtaining a Token

Tokens can be generated through:

1. **Admin UI**: Navigate to Settings → API Tokens → Generate New Token
2. **API Endpoint**: POST to `/api/auth/token`

**Example Request:**
```bash
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }'
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": "2025-12-31T23:59:59Z"
  }
}
```

#### Using the Token

Include the token in the `Authorization` header for all API requests:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  http://localhost:5000/api/agents
```

**Python Example:**
```python
import requests

headers = {
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
}

response = requests.get(
    'http://localhost:5000/api/agents',
    headers=headers
)
```

**JavaScript Example:**
```javascript
const response = await fetch('http://localhost:5000/api/agents', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN_HERE',
    'Content-Type': 'application/json'
  }
});
```

### 2. Session-Based Authentication

For web applications, session-based authentication is also supported.

**Login:**
```bash
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password"
  }' \
  -c cookies.txt
```

**Subsequent Requests:**
```bash
curl http://localhost:5000/api/agents \
  -b cookies.txt
```

## Token Management

### Token Expiration

Tokens have a configurable expiration time (default: 30 days).

**Checking Token Validity:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" \
  http://localhost:5000/api/auth/verify
```

### Refreshing Tokens

Before a token expires, you can refresh it:

```bash
curl -X POST http://localhost:5000/api/auth/refresh \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Revoking Tokens

Revoke a token when it's no longer needed:

```bash
curl -X DELETE http://localhost:5000/api/auth/token \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Authorization

### Role-Based Access Control (RBAC)

Magnet AI implements role-based permissions:

#### Roles

1. **Admin**
   - Full system access
   - User management
   - System configuration

2. **Developer**
   - Create and manage agents
   - Configure tools
   - Access API

3. **User**
   - Use agents and tools
   - View own conversations
   - Limited configuration access

4. **Viewer**
   - Read-only access
   - View dashboards
   - No modification permissions

### Permission Scopes

Tokens can be scoped to specific permissions:

**Creating a Scoped Token:**
```bash
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password",
    "scopes": ["agents:read", "conversations:write"]
  }'
```

**Available Scopes:**
- `agents:read` - View agents
- `agents:write` - Create/modify agents
- `conversations:read` - View conversations
- `conversations:write` - Create conversations
- `models:read` - View models
- `models:write` - Configure models
- `admin` - Full administrative access

### Checking Permissions

The API returns `403 Forbidden` if you lack permissions:

```json
{
  "success": false,
  "error": "Insufficient permissions",
  "required_scope": "agents:write"
}
```

## Security Best Practices

### 1. Secure Token Storage

**DO:**
- Store tokens in environment variables
- Use secure credential management systems
- Encrypt tokens at rest

**DON'T:**
- Hardcode tokens in source code
- Commit tokens to version control
- Share tokens between users

### 2. Token Rotation

Regularly rotate API tokens:
- Set reasonable expiration times
- Implement automated rotation
- Monitor token usage

### 3. HTTPS Only

Always use HTTPS in production:
```
https://your-domain.com/api/agents
```

### 4. Rate Limiting

API requests are rate-limited per token:
- 100 requests/minute (default)
- Configurable per token
- Headers include rate limit info

**Rate Limit Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### 5. IP Allowlisting

For enhanced security, restrict tokens to specific IP addresses:

```bash
curl -X POST http://localhost:5000/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{
    "username": "your_username",
    "password": "your_password",
    "allowed_ips": ["192.168.1.100", "10.0.0.50"]
  }'
```

## Authentication Errors

### Common Error Responses

**401 Unauthorized - Missing Token:**
```json
{
  "success": false,
  "error": "Authentication required",
  "code": "AUTH_REQUIRED"
}
```

**401 Unauthorized - Invalid Token:**
```json
{
  "success": false,
  "error": "Invalid token",
  "code": "INVALID_TOKEN"
}
```

**401 Unauthorized - Expired Token:**
```json
{
  "success": false,
  "error": "Token has expired",
  "code": "TOKEN_EXPIRED"
}
```

**403 Forbidden - Insufficient Permissions:**
```json
{
  "success": false,
  "error": "Insufficient permissions",
  "code": "FORBIDDEN",
  "required_scope": "agents:write"
}
```

## Environment Variables

Configure authentication settings via environment variables:

```bash
# Token expiration (in seconds)
TOKEN_EXPIRATION=2592000  # 30 days

# Secret key for token signing
SECRET_KEY=your-secret-key-here

# Enable/disable authentication
ENABLE_AUTH=true

# Rate limiting
RATE_LIMIT_PER_MINUTE=100
```

## Development vs Production

### Development Mode

For local development, authentication can be simplified:

```bash
# Disable authentication (development only!)
ENABLE_AUTH=false
```

**Warning:** Never disable authentication in production!

### Production Mode

In production:
- Always enable authentication
- Use strong secret keys
- Enable HTTPS
- Implement IP allowlisting
- Monitor authentication logs

## Next Steps

- [REST API](/docs/en/developers/api/rest-api) - API overview
- [API Endpoints](/docs/en/developers/api/endpoints) - Detailed endpoint documentation
- [Getting Started](/docs/en/developers/setup/getting-started) - Development setup
