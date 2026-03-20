# Magnet AI CLI — Reference for AI Assistants

This document describes the `magnet` CLI — a tool for managing Magnet AI resources from the command line.
It is intended as a reference for AI assistants (Claude Code, etc.) to understand how to install, configure, and use the CLI.

---

## Installation & Local Setup

### Prerequisites

- Go 1.21+ installed (`go version`)
- Access to a Magnet AI instance (local or remote)
- A Magnet AI API key

### Build and install locally (for development / Claude Code)

```bash
# From the repository root
cd cli

# Option 1: install to $GOPATH/bin (adds `magnet` to PATH permanently)
make install
# equivalent: go install -ldflags="-s -w" ./

# Option 2: build binary to cli/bin/magnet
make build
# Then add cli/bin/ to PATH, or use full path: ./bin/magnet

# Option 3: run without installing
make run ARGS="agents list"
# equivalent: go run ./ agents list
```

### Making `magnet` available to Claude Code

After `make install`, the binary lands in `$(go env GOPATH)/bin/magnet`.
Make sure `$GOPATH/bin` is in your `PATH`:

```bash
# Add to ~/.zshrc or ~/.bashrc
export PATH="$PATH:$(go env GOPATH)/bin"
```

Verify:
```bash
magnet --version
magnet --help
```

To make the CLI automatically available in Claude Code sessions, add to your project's `CLAUDE.md`:

```markdown
## Magnet AI CLI

The `magnet` binary is installed at `$(go env GOPATH)/bin/magnet`.
Use it via the Bash tool to manage Magnet AI resources.

Required environment variables (set before using):
- MAGNET_API_KEY — your Magnet AI API key
- MAGNET_BASE_URL — Magnet AI instance URL (default: http://localhost:8000)
```

---

## Configuration

### Config file: `~/.magnet/config.yaml`

```yaml
base_url: https://magnet.yourcompany.com
api_key: sk-your-api-key-here
output: table   # table | json | yaml
```

### Environment variables

```bash
export MAGNET_BASE_URL=https://magnet.yourcompany.com
export MAGNET_API_KEY=sk-your-api-key-here
```

### Priority (highest to lowest)

```
CLI flags  >  environment variables  >  ~/.magnet/config.yaml  >  defaults
```

### Global flags (available on every command)

| Flag | Default | Description |
|------|---------|-------------|
| `--api-key` | — | API key (overrides `MAGNET_API_KEY`) |
| `--base-url` | `http://localhost:8000` | Base URL (overrides `MAGNET_BASE_URL`) |
| `--output` | `table` | Output format: `table` \| `json` \| `yaml` |

---

## Command Reference

### Syntax

```
magnet <resource> <action> [arguments] [flags]
```

---

### `magnet execute` — Run an agent (single turn)

Send a message to an agent and get a response. Creates a conversation, sends the message, prints the reply.

```bash
magnet execute --agent <system-name> --message "Your message"
magnet execute -a <system-name> -m "Your message"

# Read message from stdin
echo "Summarize this document" | magnet execute --agent my-agent

# Get JSON output
magnet execute --agent my-agent --message "Hello" --output json
```

**Flags:**
| Flag | Short | Required | Description |
|------|-------|----------|-------------|
| `--agent` | `-a` | yes | Agent system name |
| `--message` | `-m` | no | Message text (reads from stdin if omitted) |

**Response format (JSON):**
```json
{
  "id": "conv-uuid",
  "agent": "my-agent",
  "messages": [
    {"role": "user", "content": "Your message"},
    {"role": "assistant", "content": "Agent reply text"}
  ],
  "last_message": {"role": "assistant", "content": "Agent reply text"},
  "created_at": "2024-01-01T00:00:00Z"
}
```

In `table` mode (default), only the assistant's reply text is printed.

---

### `magnet chat` — Interactive chat session

Start a multi-turn REPL session with an agent.

```bash
magnet chat --agent <system-name>
magnet chat -a my-agent
```

Type messages and press Enter. Type `exit` or `quit` to end the session.

**API flow:**
1. First message → `POST /api/user/agent_conversations` (creates conversation)
2. Subsequent messages → `POST /api/user/agent_conversations/{id}/messages`

---

### `magnet agents` — Manage agents

```bash
magnet agents list                          # list all agents
magnet agents get <id>                      # get agent details by ID
magnet agents create -f agent.yaml          # create from YAML/JSON file
magnet agents update <id> -f agent.yaml     # update from YAML/JSON file
magnet agents delete <id>                   # delete agent
```

**API:** `/api/admin/agents`

**Agent YAML schema:**
```yaml
name: my-agent
description: "What this agent does"
system_prompt: "You are a helpful assistant..."
model_id: "uuid-of-model"
is_active: true
```

**List response (JSON):**
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "my-agent",
      "description": "Agent description",
      "is_active": true
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 200
}
```

---

### `magnet kg` — Manage knowledge graphs

Alias: `magnet knowledge-graphs`

```bash
magnet kg list
magnet kg get <id>
magnet kg create -f kg.yaml
magnet kg update <id> -f kg.yaml
magnet kg delete <id>
magnet kg search <id> "search query"        # semantic search
magnet kg search <id> "query" --top-k 10 --threshold 0.5
```

**API:** `/api/admin/knowledge_graphs` (CRUD), `/api/user/knowledge_graph/{id}/chunks/search` (search)

**Search flags:**
| Flag | Default | Description |
|------|---------|-------------|
| `--top-k` | `5` | Number of results to return |
| `--threshold` | `0.0` | Minimum similarity score (0.0–1.0) |

**Search request body:**
```json
{
  "query": "search query text",
  "limit": 5,
  "min_score": 0.0
}
```

**Search response:**
```json
{
  "items": [
    {
      "id": "chunk-uuid",
      "content": "Relevant text chunk...",
      "score": 0.87,
      "metadata": {}
    }
  ]
}
```

---

### `magnet collections` — Manage collections

```bash
magnet collections list
magnet collections get <id>
magnet collections create -f collection.yaml
magnet collections update <id> -f collection.yaml
magnet collections delete <id>
```

**API:** `/api/admin/collections`

---

### `magnet apps` — Manage AI apps

```bash
magnet apps list
magnet apps get <id>
magnet apps create -f app.yaml
magnet apps update <id> -f app.yaml
magnet apps delete <id>
```

**API:** `/api/admin/ai_apps`

---

### `magnet prompts` — Manage prompt templates

```bash
magnet prompts list
magnet prompts get <id>
magnet prompts create -f prompt.yaml
magnet prompts update <id> -f prompt.yaml
magnet prompts delete <id>
```

**API:** `/api/admin/prompt_templates`

---

### `magnet providers` — Manage LLM providers

```bash
magnet providers list
magnet providers get <id>
magnet providers create -f provider.yaml
magnet providers update <id> -f provider.yaml
magnet providers delete <id>
```

**API:** `/api/admin/providers`

---

### `magnet models` — Manage LLM models

```bash
magnet models list
magnet models get <id>
magnet models create -f model.yaml
magnet models update <id> -f model.yaml
magnet models delete <id>
```

**API:** `/api/admin/models`

---

### `magnet api-keys` — Manage API keys

```bash
magnet api-keys list
magnet api-keys get <id>
magnet api-keys create -f key.yaml
magnet api-keys update <id> -f key.yaml
magnet api-keys delete <id>
```

**API:** `/api/admin/api_keys`

---

### `magnet rag` — Manage retrieval tools

```bash
magnet rag list
magnet rag get <id>
magnet rag create -f tool.yaml
magnet rag update <id> -f tool.yaml
magnet rag delete <id>
```

**API:** `/api/admin/retrieval_tools`

---

### `magnet mcp` — Manage MCP servers

```bash
magnet mcp list
magnet mcp get <id>
magnet mcp create -f server.yaml
magnet mcp update <id> -f server.yaml
magnet mcp delete <id>
```

**API:** `/api/admin/mcp_servers`

---

### `magnet api-servers` — Manage API servers

```bash
magnet api-servers list
magnet api-servers get <id>
magnet api-servers create -f server.yaml
magnet api-servers update <id> -f server.yaml
magnet api-servers delete <id>
```

**API:** `/api/admin/api_servers`

---

### `magnet transfer` — Export and import configuration

```bash
# Export all resources to a JSON file
magnet transfer export                          # saves to magnet-export-<timestamp>.json
magnet transfer export --output backup.json     # custom file name

# Import from a JSON file
magnet transfer import backup.json
magnet transfer import backup.json --dry-run    # preview without making changes
```

**API:** `POST /api/admin/transfer/export/json`, `POST /api/admin/transfer/import/json`

---

### `magnet apply` — GitOps-style idempotent apply

Apply one or more resource manifest files. Creates resources that don't exist, updates those that do (matched by `name`).

```bash
magnet apply -f agent.yaml
magnet apply -f ./configs/               # apply all YAML/JSON files in directory
magnet apply -f agent.yaml -f kg.yaml   # multiple files
magnet apply -f ./configs/ --dry-run    # preview without making changes
```

**Manifest format:**
```yaml
kind: agent          # resource type (see supported kinds below)
metadata:
  name: my-agent     # used to find existing resource for update
spec:
  description: "My agent"
  model_id: "uuid-of-model"
  system_prompt: "You are a helpful assistant."
  is_active: true
```

**Supported `kind` values:**
- `agent`
- `collection`
- `knowledge_graph`
- `ai_app`
- `prompt`
- `provider`
- `model`
- `api_key`
- `retrieval_tool`
- `mcp_server`
- `api_server`

**Flags:**
| Flag | Short | Description |
|------|-------|-------------|
| `--file` | `-f` | Path to manifest file or directory (repeatable) |
| `--dry-run` | — | Show what would be applied without making changes |

---

## Output Formats

All commands support `--output table|json|yaml` (or set via `MAGNET_OUTPUT` / config file).

```bash
magnet agents list --output json   # machine-readable JSON
magnet agents list --output yaml   # YAML format
magnet agents list                 # default: human-readable table
```

Use `--output json` when you need to parse command output programmatically (e.g., extract IDs).

**Extracting an agent ID with shell:**
```bash
magnet agents list --output json | jq -r '.[] | select(.name=="my-agent") | .id'
```

---

## Common Workflows for AI Assistants

### 1. Run a quick query against an agent

```bash
magnet execute --agent my-agent --message "What is the status of project X?"
```

### 2. Find an agent by name, then query it

```bash
# List agents to find the system name
magnet agents list

# Execute with the agent's system name (not UUID)
magnet execute --agent customer-support --message "How do I reset my password?"
```

### 3. Search a knowledge graph

```bash
# List KGs to find the ID
magnet kg list --output json

# Search with a semantic query
magnet kg search <kg-id> "quarterly revenue targets" --top-k 5
```

### 4. Create a resource from a manifest

```bash
# Create an agent
cat > /tmp/agent.yaml << 'EOF'
name: my-new-agent
description: "Handles customer support queries"
model_id: "gpt-4o-uuid-here"
system_prompt: "You are a helpful customer support agent."
is_active: true
EOF

magnet agents create -f /tmp/agent.yaml
```

### 5. Apply a full configuration directory (GitOps)

```bash
magnet apply -f ./magnet-configs/ --dry-run   # preview
magnet apply -f ./magnet-configs/             # apply
```

### 6. Backup and restore

```bash
# Backup
magnet transfer export --output backup-$(date +%Y%m%d).json

# Restore to another instance
MAGNET_BASE_URL=https://staging.example.com magnet transfer import backup-20240101.json
```

---

## API Authentication

All requests use `x-api-key` header:
```
x-api-key: <your-api-key>
```

The key is read from (in priority order):
1. `--api-key` flag
2. `MAGNET_API_KEY` environment variable
3. `api_key` field in `~/.magnet/config.yaml`

---

## Error Handling

The CLI exits with code `0` on success, non-zero on error.
Errors are printed to stderr.

Common errors:
- `API key is not set` — set `MAGNET_API_KEY` or use `--api-key`
- `API error 404` — resource not found (check the ID)
- `API error 401` — invalid API key
- `API error 422` — validation error (check request body fields)
- `cannot read file` — file path is wrong or file doesn't exist

---

## Notes for AI Assistants

- Agent references use **system name** (slug), not UUID, in `execute` and `chat` commands
- CRUD commands (`get`, `update`, `delete`) use **UUID**
- Use `--output json` to get structured data you can parse
- The `apply` command is idempotent — safe to run multiple times
- `transfer export/import` is for full configuration backup, not data
- Knowledge graph `search` uses semantic similarity, not keyword matching
