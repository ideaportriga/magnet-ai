# Permissions reference

Every permission code is a `verb:resource` string. The verb is the
action; the resource is the object the action is performed on. The
canonical list lives in the `Permission` enum
(`api/src/guards/permissions.py`); the table below mirrors it and
adds a one-line note on what each code unlocks in the admin UI.

::: tip
You don't need to memorise this list. The
[permission matrix](./roles#editing-the-permission-matrix) on every
role's detail page renders the whole catalog as a grid of checkboxes
grouped by resource.
:::

## Verbs

| Verb | Meaning |
|---|---|
| `read` | List the resource and view individual records. |
| `write` | Create new records and edit existing ones. |
| `delete` | Remove records permanently. |
| `execute` | Run / invoke the resource (e.g. start an agent conversation). |
| `share` | Change a record's visibility or add a resource-access grant. |
| `manage` | Administrative super-verb. Currently used for `manage:users` and `manage:resource_access`. |

## Resources

### Agents

| Code | Effect |
|---|---|
| `read:agents` | See the agents list and detail pages. |
| `write:agents` | Create and edit agents. |
| `delete:agents` | Delete agents. |
| `execute:agents` | Start a chat session with an agent. |
| `share:agents` | Change agent visibility and grant access to other principals. |

### AI Apps, Collections, Prompts

| Code | Effect |
|---|---|
| `read:ai_apps` / `write:ai_apps` / `delete:ai_apps` | Manage AI Apps. |
| `read:collections` / `write:collections` / `delete:collections` | Manage Collections. |
| `read:prompts` / `write:prompts` / `delete:prompts` | Manage Prompt Templates. |

### Knowledge Graph & RAG

| Code | Effect |
|---|---|
| `read:knowledge_graph` / `write:knowledge_graph` / `delete:knowledge_graph` | Manage the Knowledge Graph: content profiles, entity extraction, metadata, data explorer. |
| `read:rag_tools` / `write:rag_tools` / `delete:rag_tools` | Manage RAG tools (retrieval + generation pipelines, test sets, answer evaluation). |
| `read:retrieval_tools` / `write:retrieval_tools` / `delete:retrieval_tools` | Manage Retrieval tools (search-only configurations). |

### MCP & API integrations

| Code | Effect |
|---|---|
| `read:mcp_servers` / `write:mcp_servers` / `delete:mcp_servers` | Manage MCP server connections. |
| `read:api_servers` / `write:api_servers` / `delete:api_servers` | Manage external API tool definitions. |

### Evaluations, Deep Research, Prompt Queue

| Code | Effect |
|---|---|
| `read:evaluations` / `write:evaluations` | Run and manage evaluation jobs. |
| `read:deep_research` / `write:deep_research` | Manage Deep Research configs and runs. |
| `read:prompt_queue` / `write:prompt_queue` | Manage the Prompt Queue. |

### Files & Jobs

| Code | Effect |
|---|---|
| `read:files` / `write:files` | List, upload, delete files in the file store. |
| `read:jobs` / `write:jobs` | View and cancel background jobs. |

### Observability

| Code | Effect |
|---|---|
| `read:observability` | Open Observability → Traces and the Usage dashboards. |

### Note Taker

| Code | Effect |
|---|---|
| `read:note_taker` | View transcripts and recordings. |
| `write:note_taker` | Upload / edit transcripts; manage Note Taker settings. |

### AI Models & Providers

| Code | Effect |
|---|---|
| `read:ai_models` / `write:ai_models` | Manage Model Configurations. |
| `read:providers` / `write:providers` | Manage Model Providers (API keys for OpenAI, Azure, …). |

### Platform settings

| Code | Effect |
|---|---|
| `read:settings` / `write:settings` | Read / write platform configuration. Includes import-export. |

### Governance

| Code | Effect |
|---|---|
| `read:roles` | List roles, view role details. |
| `write:roles` | Create custom roles, edit and delete them, replace their permissions. |
| `read:users` | List users, view profile detail pages. |
| `manage:users` | Assign or revoke roles for any user in the tenant. |
| `read:groups` / `write:groups` | List and manage user groups. |
| `read:api_keys` / `write:api_keys` | List and manage API keys. |
| `manage:resource_access` | Create or revoke resource-access grants on any record. |
| `read:audit` | Open the Access log. |

## System role contents

For reference, the three built-in roles map to these permissions:

- **admin** — every code above.
- **user** — `read:agents`, `execute:agents`, `read:ai_apps`,
  `read:collections`, `read:prompts`, `read:knowledge_graph`,
  `read:rag_tools`, `read:retrieval_tools`, `read:mcp_servers`,
  `read:api_servers`, `read:files`, `write:files`, `read:jobs`,
  `read:ai_models`, `read:note_taker`, `write:note_taker`.
- **viewer** — every `read:*` permission, nothing else.

The defaults are seeded by migration `c5d6e7f8a9b0`; the table also
acts as the in-code fallback at boot when the cache hasn't loaded
yet (`SYSTEM_ROLE_DEFAULTS` in `api/src/guards/permissions.py`).

## API keys vs role permissions

Unlike user sessions, **API keys carry their own scopes** rather
than inheriting the owning user's role permissions. The scopes are a
capability ceiling that cannot be exceeded — even if the owner is
later granted more rights, the key won't pick them up. This protects
production keys from accidental privilege escalation. Manage scopes
in **System → API keys**.
