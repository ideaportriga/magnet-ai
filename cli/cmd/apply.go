package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strings"

	"magnet-ai/cli/internal/client"
	"magnet-ai/cli/internal/config"

	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

// resourceKindMap maps 'kind' field values to their API paths.
var resourceKindMap = map[string]string{
	"agent":          "/api/admin/agents",
	"collection":     "/api/admin/collections",
	"knowledge_graph": "/api/admin/knowledge_graphs",
	"ai_app":         "/api/admin/ai_apps",
	"prompt":         "/api/admin/prompt_templates",
	"provider":       "/api/admin/providers",
	"model":          "/api/admin/models",
	"api_key":        "/api/admin/api_keys",
	"retrieval_tool": "/api/admin/retrieval_tools",
	"mcp_server":     "/api/admin/mcp_servers",
	"api_server":     "/api/admin/api_servers",
}

// applyManifest represents a Magnet AI resource manifest.
type applyManifest struct {
	Kind     string         `yaml:"kind" json:"kind"`
	Metadata applyMetadata  `yaml:"metadata" json:"metadata"`
	Spec     map[string]any `yaml:"spec" json:"spec"`
}

type applyMetadata struct {
	Name string `yaml:"name" json:"name"`
}

var applyCmd = &cobra.Command{
	Use:   "apply",
	Short: "Apply resource manifests (idempotent create-or-update)",
	Long: `Apply one or more resource manifest files.

Reads YAML/JSON files and creates or updates resources idempotently.
If a resource with the same name exists, it is updated; otherwise created.

Manifest format:
  kind: agent
  metadata:
    name: my-agent
  spec:
    description: "My agent"
    model_id: "..."
    system_prompt: "..."

Examples:
  magnet apply -f agent.yaml
  magnet apply -f ./configs/          # apply all YAML files in directory
  magnet apply -f agent.yaml -f kg.yaml  # multiple files`,
	RunE: func(cmd *cobra.Command, args []string) error {
		files, _ := cmd.Flags().GetStringArray("file")
		dryRun, _ := cmd.Flags().GetBool("dry-run")

		if len(files) == 0 {
			return fmt.Errorf("at least one --file (-f) is required")
		}

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var allPaths []string
		for _, f := range files {
			paths, err := expandPath(f)
			if err != nil {
				return err
			}
			allPaths = append(allPaths, paths...)
		}

		if len(allPaths) == 0 {
			return fmt.Errorf("no YAML/JSON files found")
		}

		applied, skipped, failed := 0, 0, 0
		for _, path := range allPaths {
			action, err := applyFile(c, path, dryRun)
			if err != nil {
				fmt.Fprintf(os.Stderr, "  ✗ %s: %v\n", path, err)
				failed++
			} else {
				fmt.Printf("  ✓ %s (%s)\n", path, action)
				if action == "skipped" {
					skipped++
				} else {
					applied++
				}
			}
		}

		fmt.Printf("\nApplied: %d, Skipped: %d, Failed: %d\n", applied, skipped, failed)
		if failed > 0 {
			return fmt.Errorf("%d resource(s) failed to apply", failed)
		}
		return nil
	},
}

// expandPath returns all YAML/JSON files for a given path (file or directory).
func expandPath(path string) ([]string, error) {
	info, err := os.Stat(path)
	if err != nil {
		return nil, fmt.Errorf("cannot access %s: %w", path, err)
	}
	if !info.IsDir() {
		return []string{path}, nil
	}

	// Walk directory for .yaml/.yml/.json files
	var paths []string
	entries, err := os.ReadDir(path)
	if err != nil {
		return nil, err
	}
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		name := e.Name()
		ext := strings.ToLower(filepath.Ext(name))
		if ext == ".yaml" || ext == ".yml" || ext == ".json" {
			paths = append(paths, filepath.Join(path, name))
		}
	}
	return paths, nil
}

// applyFile processes a single manifest file.
func applyFile(c *client.Client, path string, dryRun bool) (string, error) {
	data, err := os.ReadFile(path)
	if err != nil {
		return "", fmt.Errorf("cannot read: %w", err)
	}

	var manifest applyManifest
	ext := strings.ToLower(filepath.Ext(path))
	if ext == ".json" {
		if err := json.Unmarshal(data, &manifest); err != nil {
			return "", fmt.Errorf("invalid JSON: %w", err)
		}
	} else {
		if err := yaml.Unmarshal(data, &manifest); err != nil {
			return "", fmt.Errorf("invalid YAML: %w", err)
		}
	}

	if manifest.Kind == "" {
		return "", fmt.Errorf("missing 'kind' field")
	}
	if manifest.Metadata.Name == "" {
		return "", fmt.Errorf("missing 'metadata.name' field")
	}

	basePath, ok := resourceKindMap[strings.ToLower(manifest.Kind)]
	if !ok {
		return "", fmt.Errorf("unknown kind %q (supported: %s)", manifest.Kind, strings.Join(supportedKinds(), ", "))
	}

	if dryRun {
		return fmt.Sprintf("dry-run: would apply %s/%s", manifest.Kind, manifest.Metadata.Name), nil
	}

	// Find existing resource by name
	existingID, err := findResourceByName(c, basePath, manifest.Metadata.Name)
	if err != nil {
		return "", fmt.Errorf("lookup failed: %w", err)
	}

	// Merge name into spec body
	body := make(map[string]any)
	for k, v := range manifest.Spec {
		body[k] = v
	}
	body["name"] = manifest.Metadata.Name

	var result map[string]any
	if existingID != "" {
		if err := c.Update(basePath+"/"+existingID, body, &result); err != nil {
			return "", fmt.Errorf("update failed: %w", err)
		}
		return "updated", nil
	}

	if err := c.Create(basePath, body, &result); err != nil {
		return "", fmt.Errorf("create failed: %w", err)
	}
	return "created", nil
}

// findResourceByName searches for a resource by name and returns its ID if found.
func findResourceByName(c *client.Client, basePath, name string) (string, error) {
	var result struct {
		Items []struct {
			ID   string `json:"id"`
			Name string `json:"name"`
		} `json:"items"`
	}
	if err := c.List(basePath, map[string]string{"page_size": "500"}, &result); err != nil {
		return "", err
	}
	for _, item := range result.Items {
		if item.Name == name {
			return item.ID, nil
		}
	}
	return "", nil
}

func supportedKinds() []string {
	kinds := make([]string, 0, len(resourceKindMap))
	for k := range resourceKindMap {
		kinds = append(kinds, k)
	}
	return kinds
}

func init() {
	applyCmd.Flags().StringArrayP("file", "f", nil, "Path to manifest file or directory (can be repeated)")
	applyCmd.Flags().Bool("dry-run", false, "Show what would be applied without making changes")

	rootCmd.AddCommand(applyCmd)
}
