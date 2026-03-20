# Magnet AI CLI

`magnet` is a command-line tool for managing [Magnet AI](https://github.com/ideaportriga/magnet-ai) resources — agents, knowledge graphs, collections, models, and more — via the REST API.

```
magnet agents list
magnet execute --agent my-agent --message "Summarize Q4 results"
magnet kg search <kg-id> "quarterly revenue"
magnet apply -f ./configs/
```

---

## Installation

### Requirements

- [Go 1.21+](https://go.dev/dl/)
- Access to a running Magnet AI instance
- A valid Magnet AI API key

### Install from source

```bash
git clone https://github.com/ideaportriga/magnet-ai.git
cd magnet-ai/cli

# Install binary to $GOPATH/bin (adds `magnet` to your PATH)
make install
```

Make sure `$GOPATH/bin` is in your `PATH`. Add this to your `~/.zshrc` or `~/.bashrc` if it isn't:

```bash
export PATH="$PATH:$(go env GOPATH)/bin"
```

Verify the installation:

```bash
magnet --version
magnet --help
```

### Build without installing

```bash
cd magnet-ai/cli
make build
# binary is created at cli/bin/magnet
./bin/magnet --help
```

### Development (run without building)

```bash
cd magnet-ai/cli
make run ARGS="agents list"
# equivalent: go run ./ agents list
```

---

## Configuration

The CLI needs two things to connect to your Magnet AI instance: a **base URL** and an **API key**.

### Option 1 — Environment variables (recommended)

```bash
export MAGNET_BASE_URL=https://magnet.yourcompany.com
export MAGNET_API_KEY=sk-your-api-key-here
```

### Option 2 — Config file

Create `~/.magnet/config.yaml`:

```yaml
base_url: https://magnet.yourcompany.com
api_key: sk-your-api-key-here
output: table   # table | json | yaml (default: table)
```

### Option 3 — CLI flags (per-command override)

```bash
magnet agents list --base-url https://magnet.yourcompany.com --api-key sk-...
```

### Priority order

```
CLI flags  >  environment variables  >  ~/.magnet/config.yaml  >  defaults
```

Default `base_url` is `http://localhost:8000` (local development).

---

## Usage

### Global flags

Every command accepts these flags:

| Flag | Description |
|------|-------------|
| `--output table\|json\|yaml` | Output format (default: `table`) |
| `--api-key <key>` | Override API key |
| `--base-url <url>` | Override base URL |

---

### Running an agent

Send a single message to an agent and get a response:

```bash
magnet execute --agent my-agent --message "What is the status of project X?"

# Short flags
magnet execute -a my-agent -m "Hello"

# Read message from stdin
echo "Summarize this" | magnet execute --agent my-agent

# Get structured JSON output
magnet execute --agent my-agent --message "Hello" --output json
```

> The `--agent` flag takes the agent's **system name** (slug), not its UUID.

### Interactive chat session

Start a multi-turn conversation with an agent:

```bash
magnet chat --agent my-agent
```

Type your messages and press Enter. Type `exit` or `quit` to end the session.

---

### Managing resources

All resources follow the same pattern:

```bash
magnet <resource> list
magnet <resource> get <id>
magnet <resource> create -f file.yaml
magnet <resource> update <id> -f file.yaml
magnet <resource> delete <id>
```

**Available resources:**

| Command | Description |
|---------|-------------|
| `magnet agents` | AI agents |
| `magnet kg` | Knowledge graphs (alias: `knowledge-graphs`) |
| `magnet collections` | Document collections |
| `magnet apps` | AI apps |
| `magnet prompts` | Prompt templates |
| `magnet providers` | LLM providers |
| `magnet models` | AI models (alias: `ai-models`) |
| `magnet api-keys` | API keys |
| `magnet rag` | Retrieval tools |
| `magnet mcp` | MCP servers |
| `magnet api-servers` | API servers |

**Examples:**

```bash
# List all agents
magnet agents list

# Get agent details
magnet agents get 550e8400-e29b-41d4-a716-446655440000

# Create an agent from a YAML file
magnet agents create -f agent.yaml

# Update an agent
magnet agents update 550e8400-e29b-41d4-a716-446655440000 -f agent.yaml

# Delete an agent
magnet agents delete 550e8400-e29b-41d4-a716-446655440000
```

### Resource file format (YAML or JSON)

```yaml
name: my-agent
description: "Handles customer support queries"
system_prompt: "You are a helpful customer support assistant."
model_id: "uuid-of-the-model"
is_active: true
```

---

### Knowledge graph search

Perform semantic search within a knowledge graph:

```bash
magnet kg search <kg-id> "quarterly revenue targets"

# Control result count and similarity threshold
magnet kg search <kg-id> "project deadlines" --top-k 10 --threshold 0.6
```

| Flag | Default | Description |
|------|---------|-------------|
| `--top-k` | `5` | Number of results to return |
| `--threshold` | `0.0` | Minimum similarity score (0.0–1.0) |

---

### GitOps: `apply`

Idempotent create-or-update from manifest files. If a resource with the same `name` exists it will be updated, otherwise created.

```bash
# Apply a single file
magnet apply -f agent.yaml

# Apply all YAML/JSON files in a directory
magnet apply -f ./configs/

# Apply multiple files
magnet apply -f agent.yaml -f kg.yaml

# Preview without making changes
magnet apply -f ./configs/ --dry-run
```

**Manifest format:**

```yaml
kind: agent           # resource type
metadata:
  name: my-agent      # used to find existing resource
spec:
  description: "My agent"
  model_id: "uuid-of-the-model"
  system_prompt: "You are a helpful assistant."
  is_active: true
```

Supported `kind` values: `agent`, `collection`, `knowledge_graph`, `ai_app`, `prompt`, `provider`, `model`, `api_key`, `retrieval_tool`, `mcp_server`, `api_server`.

---

### Export and import configuration

Back up all resources to a JSON file and restore them on another instance:

```bash
# Export everything
magnet transfer export
magnet transfer export --output backup.json

# Import from backup
magnet transfer import backup.json

# Preview import without making changes
magnet transfer import backup.json --dry-run
```

---

## Output formats

Use `--output json` or `--output yaml` for machine-readable output:

```bash
magnet agents list --output json
magnet agents list --output yaml

# Extract a field with jq
magnet agents list --output json | jq -r '.[] | select(.name=="my-agent") | .id'
```

---

## Using with Claude Code

After installing the binary (`make install`), Claude Code can call `magnet` commands via the Bash tool.

Add the following to your project's `CLAUDE.md` to make it available in every session:

```markdown
## Magnet AI CLI

Use the `magnet` CLI to interact with the Magnet AI instance.

Setup:
- Binary: installed at `$(go env GOPATH)/bin/magnet`
- Set `MAGNET_API_KEY` and `MAGNET_BASE_URL` before running commands

Common commands:
- `magnet agents list` — list available agents
- `magnet execute --agent <name> --message "..."` — run an agent
- `magnet kg search <id> "query"` — search a knowledge graph
- `magnet apply -f ./configs/` — apply resource manifests

See `cli/CLI_REFERENCE.md` for full command reference and response formats.
```

For detailed request/response formats and AI assistant usage patterns, see [CLI_REFERENCE.md](./CLI_REFERENCE.md).

---

## Development

```bash
cd cli

# Build
make build

# Run tests
make test

# Lint
make lint

# Build for all platforms
make build-all

# Clean build artifacts
make clean
```

Cross-platform binaries are output to `dist/`:
- `magnet-linux-amd64`
- `magnet-linux-arm64`
- `magnet-darwin-amd64`
- `magnet-darwin-arm64`
- `magnet-windows-amd64.exe`
