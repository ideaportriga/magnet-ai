# MCP server

Magnet ships with an **embedded Model Context Protocol (MCP)
server** that exposes a curated subset of platform APIs to MCP
clients — Claude Desktop, Claude apps, the MCP Inspector,
Postman, or any custom client. Once enabled, Magnet additionally
acts as an **OAuth 2.1 authorization server** so connecting
clients can authenticate users and inherit their permissions.

::: tip
"MCP server" here means *Magnet exposes its tools to external
clients*. **MCP Tools** in the sidebar refers to the inverse —
Magnet connecting *out* to other people's MCP servers as a
client. The two share concepts but are independent features.
:::

## What's exposed

The embedded server registers four tool groups, each requiring
the matching read permission from the calling user:

| Group | Sample tools | Required perms |
|---|---|---|
| **Prompt templates** | `prompt_templates_list`, `prompt_template_get`, `prompt_template_variant_get` | `read:prompts` |
| **Prompt execution** | `prompt_template_run` | `read:prompts` + `execute:agents` |
| **LLM monitoring** | `llm_usage_summary`, `llm_calls_list` | `read:observability` |
| **Evaluations** | `evaluation_sets_list`, `evaluation_set_get`, `evaluation_set_create`, `evaluations_list`, `evaluation_run` | `read:evaluations`, `write:evaluations` |

Each tool call runs through the same RBAC pipeline as the REST
API. A user without the matching permission gets a 403 from the
MCP server, identical to direct API behaviour.

## Enabling the server

In your `.env`:

```bash
MCP_ENABLED=true

# Public origin of the OAuth authorization server (Magnet itself).
# HTTPS required, except for localhost in dev.
MCP_ISSUER_URL=https://magnet.example.com

# Canonical URI of the MCP resource server, stamped as the `aud`
# claim on every access token (RFC 8707).
MCP_AUDIENCE=https://magnet.example.com/mcp

# Where unauthenticated users are sent to log in before the
# /authorize redirect completes.
MCP_LOGIN_URL=/admin/login
```

When `MCP_ENABLED=true`, Magnet additionally serves:

- `/.well-known/oauth-authorization-server` — issuer metadata.
- `/.well-known/oauth-protected-resource` — resource server
  metadata.
- `/authorize`, `/token` — OAuth 2.1 endpoints.
- `/mcp` — the JSON-RPC transport endpoint clients call into.

Optional tuning:

| Variable | Default | Notes |
|---|---|---|
| `MCP_AUTH_CODE_TTL_SECONDS` | `300` | Authorization-code lifetime; OAuth recommends ≤10 min. |
| `MCP_PENDING_STATE_TTL_SECONDS` | `600` | Signed JWT carrying `/authorize` state across the SSO chain. |

## Managing OAuth clients

Each MCP client (Claude Desktop, an internal automation, …) is
registered as an OAuth client. Open
**System → OAuth Clients (MCP)** in the admin sidebar — visible
to users with `write:roles`, which by default means tenant
admins.

Register a client by giving it:

- A **name** (shown to users on the consent screen).
- A list of **redirect URIs**. Claude Desktop uses
  `claude-mcp://oauth/callback`.
- A list of **allowed scopes** — the union of MCP tool groups it
  is permitted to ask for.

Magnet generates a client ID and, optionally, a client secret.
Public clients (Claude Desktop and other native apps that can't
keep a secret) should be registered as PKCE-only.

## Connecting Claude

In Claude Desktop's configuration, add Magnet as an MCP server:

```json
{
  "mcpServers": {
    "magnet-ai": {
      "type": "http",
      "url": "https://magnet.example.com/mcp"
    }
  }
}
```

On first use, Claude opens Magnet's `/authorize` page. The user
logs in (re-using any existing browser session), consents to the
requested scopes, and is redirected back to Claude with an
authorization code. Subsequent tool calls carry the resulting
access token automatically.

## Security model

A few invariants are worth knowing as an admin:

- **Audience binding** — every access token is bound to your
  configured `MCP_AUDIENCE`. A token for one Magnet
  deployment can't be replayed against another.
- **No cross-tenant leakage** — tools resolve the user's home
  tenant from the token; record-level RBAC applies the same way
  as in the admin UI.
- **DNS-rebinding protection** — the `/mcp` endpoint validates
  the `Host` header against the configured issuer. Local
  development of the MCP Inspector needs
  `CORS_OVERRIDE_ALLOWED_ORIGINS` set; see `.env.example`.
- **No password / secret exposure** — tools never return raw
  credentials, even to admins. Provider secrets remain encrypted
  with `SECRET_ENCRYPTION_KEY`.

## Observability

MCP requests produce the same trace IDs as the REST API. Filter
on `mcp` in **Observability → Traces** to see only MCP-driven
runs. Failed authorization attempts and consented client grants
are written to the [access log](../access/access-log) under the
action codes `mcp.client.consent` and `mcp.auth.failure`.

## Disabling

Setting `MCP_ENABLED=false` (or unsetting it) immediately removes
the OAuth and MCP routes from the API. Existing access tokens
will continue to validate signatures locally until they expire,
but every `/mcp` call returns 404. Restart workers + the API
process after toggling.
