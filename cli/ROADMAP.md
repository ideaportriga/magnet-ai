# Magnet AI CLI — Go Implementation Roadmap

## Overview

`magnet` — Go CLI для управления Magnet AI через REST API. Устанавливается как единый бинарник, работает в Claude Code / CI / скриптах.

```
magnet [resource] [action] [flags]

magnet agents list
magnet agents get <id>
magnet agents create --file agent.yaml
magnet execute --agent <id> --message "Summarize this"
magnet kg search <id> "query"
```

---

## Монорепо: структура после добавления `cli/`

```
magnet-ai/
├── api/          # Python / Litestar
├── web/          # Vue.js / Nx
├── cli/          # Go CLI  ← новая папка
│   ├── cmd/
│   │   ├── root.go
│   │   ├── agents.go
│   │   ├── collections.go
│   │   ├── knowledge_graphs.go
│   │   ├── ai_apps.go
│   │   ├── prompts.go
│   │   ├── providers.go
│   │   ├── models.go
│   │   ├── api_keys.go
│   │   ├── retrieval_tools.go
│   │   ├── mcp_servers.go
│   │   ├── api_servers.go
│   │   ├── execute.go
│   │   ├── chat.go
│   │   └── transfer.go
│   ├── internal/
│   │   ├── client/
│   │   │   ├── client.go      # resty HTTP client
│   │   │   └── errors.go
│   │   ├── config/
│   │   │   └── config.go      # viper: env + ~/.magnet/config.yaml
│   │   └── output/
│   │       └── output.go      # table / json / yaml formatter
│   ├── main.go
│   ├── go.mod                 # module magnet-ai/cli
│   ├── go.sum
│   ├── Makefile
│   └── .goreleaser.yaml
├── package.json               # добавить cli:* scripts
├── .github/workflows/
│   ├── ci.yml                 # добавить cli-checks job
│   └── cli-release.yml        # новый workflow для бинарников
└── ...
```

---

## Фазы реализации

### Фаза 1 — Scaffold & Core Infrastructure (1–2 дня)

**Цель**: проект компилируется, читает конфиг, умеет делать HTTP-запросы с `x-api-key`.

#### 1.1 Инициализация Go модуля

```bash
mkdir cli && cd cli
go mod init magnet-ai/cli
go get github.com/spf13/cobra@latest
go get github.com/spf13/viper@latest
go get github.com/go-resty/resty/v2@latest
go get github.com/olekukonko/tablewriter@latest
go get gopkg.in/yaml.v3@latest
```

#### 1.2 `cli/internal/config/config.go`

```go
package config

import (
    "fmt"
    "os"
    "path/filepath"

    "github.com/spf13/viper"
)

type Config struct {
    BaseURL string `mapstructure:"base_url"`
    APIKey  string `mapstructure:"api_key"`
    Output  string `mapstructure:"output"` // table|json|yaml
}

func Load() (*Config, error) {
    viper.SetEnvPrefix("MAGNET")
    viper.AutomaticEnv()

    // ~/.magnet/config.yaml
    home, _ := os.UserHomeDir()
    viper.AddConfigPath(filepath.Join(home, ".magnet"))
    viper.SetConfigName("config")
    viper.SetConfigType("yaml")
    _ = viper.ReadInConfig()

    // env aliases
    viper.BindEnv("base_url", "MAGNET_BASE_URL")
    viper.BindEnv("api_key", "MAGNET_API_KEY")

    // defaults
    viper.SetDefault("base_url", "http://localhost:8000")
    viper.SetDefault("output", "table")

    var cfg Config
    if err := viper.Unmarshal(&cfg); err != nil {
        return nil, fmt.Errorf("config error: %w", err)
    }
    if cfg.APIKey == "" {
        return nil, fmt.Errorf("MAGNET_API_KEY is not set")
    }
    return &cfg, nil
}
```

#### 1.3 `cli/internal/client/client.go`

```go
package client

import (
    "fmt"
    "magnet-ai/cli/internal/config"

    "github.com/go-resty/resty/v2"
)

type Client struct {
    r       *resty.Client
    BaseURL string
}

func New(cfg *config.Config) *Client {
    r := resty.New().
        SetBaseURL(cfg.BaseURL).
        SetHeader("x-api-key", cfg.APIKey).
        SetHeader("Content-Type", "application/json")
    return &Client{r: r, BaseURL: cfg.BaseURL}
}

// GET /api/admin/{resource}?page=1&page_size=50
func (c *Client) List(path string, params map[string]string, out any) error {
    resp, err := c.r.R().SetQueryParams(params).SetResult(out).Get(path)
    return checkResp(resp, err)
}

// GET /api/admin/{resource}/{id}
func (c *Client) Get(path string, out any) error {
    resp, err := c.r.R().SetResult(out).Get(path)
    return checkResp(resp, err)
}

// POST /api/admin/{resource}
func (c *Client) Create(path string, body any, out any) error {
    resp, err := c.r.R().SetBody(body).SetResult(out).Post(path)
    return checkResp(resp, err)
}

// PATCH /api/admin/{resource}/{id}
func (c *Client) Update(path string, body any, out any) error {
    resp, err := c.r.R().SetBody(body).SetResult(out).Patch(path)
    return checkResp(resp, err)
}

// DELETE /api/admin/{resource}/{id}
func (c *Client) Delete(path string) error {
    resp, err := c.r.R().Delete(path)
    return checkResp(resp, err)
}

func checkResp(resp *resty.Response, err error) error {
    if err != nil {
        return fmt.Errorf("request failed: %w", err)
    }
    if resp.IsError() {
        return fmt.Errorf("API error %d: %s", resp.StatusCode(), resp.String())
    }
    return nil
}
```

#### 1.4 `cli/internal/output/output.go`

```go
package output

import (
    "encoding/json"
    "fmt"
    "os"

    "github.com/olekukonko/tablewriter"
    "gopkg.in/yaml.v3"
)

type Format string

const (
    FormatTable Format = "table"
    FormatJSON  Format = "json"
    FormatYAML  Format = "yaml"
)

func Print(format Format, headers []string, rows [][]string, data any) error {
    switch format {
    case FormatJSON:
        return printJSON(data)
    case FormatYAML:
        return printYAML(data)
    default:
        printTable(headers, rows)
        return nil
    }
}

func printTable(headers []string, rows [][]string) {
    t := tablewriter.NewWriter(os.Stdout)
    t.SetHeader(headers)
    t.SetBorder(false)
    t.SetHeaderAlignment(tablewriter.ALIGN_LEFT)
    t.SetAlignment(tablewriter.ALIGN_LEFT)
    t.AppendBulk(rows)
    t.Render()
}

func printJSON(data any) error {
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    return enc.Encode(data)
}

func printYAML(data any) error {
    b, err := yaml.Marshal(data)
    if err != nil {
        return err
    }
    fmt.Print(string(b))
    return nil
}
```

#### 1.5 `cli/cmd/root.go`

```go
package cmd

import (
    "fmt"
    "os"

    "github.com/spf13/cobra"
    "github.com/spf13/viper"
)

var outputFormat string

var rootCmd = &cobra.Command{
    Use:   "magnet",
    Short: "Magnet AI CLI",
    Long:  "Manage Magnet AI resources from the command line.",
}

func Execute() {
    if err := rootCmd.Execute(); err != nil {
        fmt.Fprintln(os.Stderr, err)
        os.Exit(1)
    }
}

func init() {
    rootCmd.PersistentFlags().StringVar(&outputFormat, "output", "table", "Output format: table|json|yaml")
    rootCmd.PersistentFlags().String("api-key", "", "API key (overrides MAGNET_API_KEY)")
    rootCmd.PersistentFlags().String("base-url", "", "Base URL (overrides MAGNET_BASE_URL)")

    viper.BindPFlag("output", rootCmd.PersistentFlags().Lookup("output"))
    viper.BindPFlag("api_key", rootCmd.PersistentFlags().Lookup("api-key"))
    viper.BindPFlag("base_url", rootCmd.PersistentFlags().Lookup("base-url"))
}
```

#### 1.6 `cli/main.go`

```go
package main

import "magnet-ai/cli/cmd"

func main() {
    cmd.Execute()
}
```

---

### Фаза 2 — CRUD команды для всех сущностей (3–4 дня)

**Цель**: полный CRUD для агентов, коллекций, KG, AI apps, промптов, провайдеров, моделей, API ключей, retrieval tools, MCP серверов.

#### Паттерн команды (пример: `cli/cmd/agents.go`)

```go
package cmd

import (
    "fmt"
    "os"
    "strings"

    "magnet-ai/cli/internal/client"
    "magnet-ai/cli/internal/config"
    "magnet-ai/cli/internal/output"

    "github.com/spf13/cobra"
    "gopkg.in/yaml.v3"
)

var agentsCmd = &cobra.Command{
    Use:   "agents",
    Short: "Manage agents",
}

var agentsListCmd = &cobra.Command{
    Use:   "list",
    Short: "List all agents",
    RunE: func(cmd *cobra.Command, args []string) error {
        cfg, err := config.Load()
        if err != nil {
            return err
        }
        c := client.New(cfg)

        var result struct {
            Items []struct {
                ID          string `json:"id"`
                Name        string `json:"name"`
                Description string `json:"description"`
                IsActive    bool   `json:"is_active"`
            } `json:"items"`
        }
        if err := c.List("/api/admin/agents", map[string]string{"page_size": "100"}, &result); err != nil {
            return err
        }

        headers := []string{"ID", "NAME", "DESCRIPTION", "ACTIVE"}
        rows := make([][]string, len(result.Items))
        for i, a := range result.Items {
            rows[i] = []string{a.ID, a.Name, truncate(a.Description, 50), fmt.Sprintf("%v", a.IsActive)}
        }

        format := output.Format(cfg.Output)
        return output.Print(format, headers, rows, result.Items)
    },
}

var agentsGetCmd = &cobra.Command{
    Use:   "get <id>",
    Short: "Get agent by ID",
    Args:  cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        cfg, err := config.Load()
        if err != nil {
            return err
        }
        c := client.New(cfg)
        var result map[string]any
        if err := c.Get("/api/admin/agents/"+args[0], &result); err != nil {
            return err
        }
        return output.Print(output.Format(cfg.Output), nil, nil, result)
    },
}

var agentsCreateCmd = &cobra.Command{
    Use:   "create",
    Short: "Create agent from YAML/JSON file",
    RunE: func(cmd *cobra.Command, args []string) error {
        file, _ := cmd.Flags().GetString("file")
        cfg, err := config.Load()
        if err != nil {
            return err
        }

        data, err := os.ReadFile(file)
        if err != nil {
            return fmt.Errorf("cannot read file: %w", err)
        }
        var body map[string]any
        if err := yaml.Unmarshal(data, &body); err != nil {
            return err
        }

        c := client.New(cfg)
        var result map[string]any
        if err := c.Create("/api/admin/agents", body, &result); err != nil {
            return err
        }
        return output.Print(output.Format(cfg.Output), nil, nil, result)
    },
}

var agentsDeleteCmd = &cobra.Command{
    Use:   "delete <id>",
    Short: "Delete agent",
    Args:  cobra.ExactArgs(1),
    RunE: func(cmd *cobra.Command, args []string) error {
        cfg, err := config.Load()
        if err != nil {
            return err
        }
        c := client.New(cfg)
        if err := c.Delete("/api/admin/agents/" + args[0]); err != nil {
            return err
        }
        fmt.Println("Deleted:", args[0])
        return nil
    },
}

func init() {
    agentsCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
    agentsCreateCmd.MarkFlagRequired("file")

    agentsCmd.AddCommand(agentsListCmd, agentsGetCmd, agentsCreateCmd, agentsDeleteCmd)
    rootCmd.AddCommand(agentsCmd)
}

func truncate(s string, n int) string {
    s = strings.ReplaceAll(s, "\n", " ")
    if len(s) > n {
        return s[:n] + "..."
    }
    return s
}
```

#### Список команд по сущностям

| Файл                       | Команда              | Эндпоинты                                    |
|----------------------------|----------------------|----------------------------------------------|
| `cmd/agents.go`            | `magnet agents`      | `/api/admin/agents`                          |
| `cmd/collections.go`       | `magnet collections` | `/api/admin/collections`                     |
| `cmd/knowledge_graphs.go`  | `magnet kg`          | `/api/admin/knowledge_graphs`                |
| `cmd/ai_apps.go`           | `magnet apps`        | `/api/admin/ai_apps`                         |
| `cmd/prompts.go`           | `magnet prompts`     | `/api/admin/prompts`                         |
| `cmd/providers.go`         | `magnet providers`   | `/api/admin/providers`                       |
| `cmd/models.go`            | `magnet models`      | `/api/admin/models`                          |
| `cmd/api_keys.go`          | `magnet api-keys`    | `/api/admin/api_keys`                        |
| `cmd/retrieval_tools.go`   | `magnet rag`         | `/api/admin/retrieval_tools`                 |
| `cmd/mcp_servers.go`       | `magnet mcp`         | `/api/admin/mcp_servers`                     |
| `cmd/api_servers.go`       | `magnet api-servers` | `/api/admin/api_servers`                     |

Каждый файл содержит подкоманды: `list`, `get <id>`, `create -f file.yaml`, `update <id> -f file.yaml`, `delete <id>`.

---

### Фаза 3 — Функциональные команды (2–3 дня)

#### 3.1 `magnet execute` — разовое выполнение агента

```go
// cmd/execute.go
var executeCmd = &cobra.Command{
    Use:   "execute",
    Short: "Execute an agent conversation",
    RunE: func(cmd *cobra.Command, args []string) error {
        agentID, _ := cmd.Flags().GetString("agent")
        message, _ := cmd.Flags().GetString("message")
        // POST /api/user/execute
        body := map[string]any{
            "agent_id": agentID,
            "messages": []map[string]any{
                {"role": "user", "content": message},
            },
        }
        // ... stream or collect response
    },
}
```

Флаги:
- `--agent <id>` — ID агента
- `--message <text>` — сообщение (или читать из stdin)
- `--stream` — стримить ответ

#### 3.2 `magnet chat` — интерактивный диалог

```go
// cmd/chat.go
// REPL loop: readline -> POST /api/user/agent_conversations/{id}/message -> print
```

#### 3.3 `magnet kg search <id> <query>` — поиск в KG

```go
// POST /api/user/knowledge_graph/{id}/search
body := KnowledgeGraphSearchRequest{
    Query:    query,
    TopK:     topK,
    Threshold: threshold,
}
```

Флаги: `--top-k 5`, `--threshold 0.7`

#### 3.4 `magnet transfer export/import` — бэкап конфигурации

```go
// cmd/transfer.go
// export: GET /api/admin/transfer/export → сохранить в файл
// import: POST /api/admin/transfer/import ← загрузить из файла
```

---

### Фаза 4 — GitOps: `apply` команда (1 день)

```bash
magnet apply -f ./magnet-config/
```

Рекурсивно читает YAML файлы, для каждого:
1. Определяет тип ресурса по полю `kind:` или директории
2. Ищет существующий ресурс по `name`
3. Создаёт если нет, обновляет если есть (idempotent)

Структура YAML файла ресурса:
```yaml
kind: agent
metadata:
  name: my-agent
spec:
  description: "..."
  model_id: "..."
  system_prompt: "..."
```

---

### Фаза 5 — Сборка и дистрибуция (1 день)

#### 5.1 `cli/Makefile`

```makefile
CLI_VERSION ?= $(shell git describe --tags --always --dirty)
BUILD_FLAGS = -ldflags="-s -w -X main.version=$(CLI_VERSION)"

.PHONY: build build-all install lint test

build:
	go build $(BUILD_FLAGS) -o bin/magnet ./

build-all:
	GOOS=linux   GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-linux-amd64 ./
	GOOS=linux   GOARCH=arm64  go build $(BUILD_FLAGS) -o dist/magnet-linux-arm64 ./
	GOOS=darwin  GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-darwin-amd64 ./
	GOOS=darwin  GOARCH=arm64  go build $(BUILD_FLAGS) -o dist/magnet-darwin-arm64 ./
	GOOS=windows GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-windows-amd64.exe ./

install:
	go install $(BUILD_FLAGS) ./

lint:
	golangci-lint run ./...

test:
	go test ./... -v
```

#### 5.2 `cli/.goreleaser.yaml`

```yaml
version: 2
project_name: magnet

builds:
  - main: ./
    dir: cli
    binary: magnet
    env:
      - CGO_ENABLED=0
    ldflags:
      - -s -w -X main.version={{.Version}}
    goos: [linux, darwin, windows]
    goarch: [amd64, arm64]
    ignore:
      - goos: windows
        goarch: arm64

archives:
  - format: tar.gz
    format_overrides:
      - goos: windows
        format: zip
    name_template: "magnet_{{ .Version }}_{{ .Os }}_{{ .Arch }}"

checksum:
  name_template: checksums.txt

brews:
  - repository:
      owner: ideaportriga
      name: homebrew-tap
    homepage: https://github.com/ideaportriga/magnet-ai
    description: Magnet AI CLI

release:
  github:
    owner: ideaportriga
    name: magnet-ai
```

---

### Фаза 6 — Интеграция в монорепо (0.5 дня)

#### 6.1 Добавить в `package.json` (корневой)

```json
{
  "scripts": {
    "setup:cli": "cd cli && go mod download",
    "build:cli": "cd cli && make build",
    "build:cli:all": "cd cli && make build-all",
    "install:cli": "cd cli && go install ./",
    "lint:cli": "cd cli && golangci-lint run ./...",
    "test:cli": "cd cli && go test ./... -v",
    "setup": "... && npm run setup:cli",
    "lint": "npm run lint:api && npm run lint:web && npm run lint:cli"
  }
}
```

#### 6.2 Добавить job в `.github/workflows/ci.yml`

```yaml
cli-checks:
  name: CLI - Build & Test
  runs-on: ubuntu-latest
  defaults:
    run:
      working-directory: ./cli

  steps:
    - uses: actions/checkout@v4

    - name: Set up Go
      uses: actions/setup-go@v5
      with:
        go-version: '1.23'
        cache-dependency-path: cli/go.sum

    - name: Build
      run: go build ./...

    - name: Test
      run: go test ./... -v

    - name: Vet
      run: go vet ./...
```

Добавить `cli-checks` в `needs` финального джоба `all-checks-complete`.

#### 6.3 Новый workflow `.github/workflows/cli-release.yml`

```yaml
name: CLI Release

on:
  push:
    tags:
      - 'v*'

jobs:
  goreleaser:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - uses: actions/setup-go@v5
        with:
          go-version: '1.23'

      - uses: goreleaser/goreleaser-action@v6
        with:
          workdir: cli
          args: release --clean
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

---

## Конфигурация пользователя

```yaml
# ~/.magnet/config.yaml
base_url: https://magnet.company.com
api_key: sk-...

output: table   # table | json | yaml
```

Или через переменные окружения:
```bash
export MAGNET_BASE_URL=https://magnet.company.com
export MAGNET_API_KEY=sk-...
```

Приоритет: `флаги CLI` > `env vars` > `config file` > `defaults`

---

## Использование в Claude Code

В `.claude/settings.json` проекта:
```json
{
  "mcpServers": {}
}
```

В системном промпте или `CLAUDE.md`:
```markdown
## Magnet AI Tools

Use `magnet` CLI to interact with Magnet AI:
- `magnet agents list` — show available agents
- `magnet execute --agent <id> --message "..."` — run agent
- `magnet kg search <kg-id> "query"` — search knowledge graph
```

Claude Code будет использовать Bash tool для вызова `magnet` команд.

---

## Итоговый план спринтов

| Спринт | Задачи                                           | Результат                        |
|--------|--------------------------------------------------|----------------------------------|
| 1      | Scaffold, config, client, output, root cmd       | `magnet --help` работает         |
| 2      | CRUD: agents, collections, kg, apps              | 4 ресурса полностью              |
| 3      | CRUD: prompts, providers, models, api-keys       | 4 ресурса полностью              |
| 4      | CRUD: rag, mcp, api-servers; execute, chat       | Все сущности + функции           |
| 5      | kg search, transfer export/import, apply cmd     | GitOps workflow                  |
| 6      | Build pipeline, GoReleaser, monorepo integration | Релиз в GitHub + Homebrew        |
