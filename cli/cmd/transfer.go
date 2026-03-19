package cmd

import (
	"encoding/json"
	"fmt"
	"os"
	"time"

	"magnet-ai/cli/internal/client"
	"magnet-ai/cli/internal/config"

	"github.com/spf13/cobra"
)

var transferCmd = &cobra.Command{
	Use:   "transfer",
	Short: "Export and import Magnet AI configuration",
}

var transferExportCmd = &cobra.Command{
	Use:   "export",
	Short: "Export all configuration to a JSON file",
	Long: `Export all Magnet AI resources (agents, knowledge graphs, collections,
providers, models, prompts, retrieval tools, MCP servers, API servers) to a JSON file.

Example:
  magnet transfer export --output backup.json
  magnet transfer export  # saves to magnet-export-<timestamp>.json`,
	RunE: func(cmd *cobra.Command, args []string) error {
		outFile, _ := cmd.Flags().GetString("output")
		if outFile == "" {
			outFile = fmt.Sprintf("magnet-export-%s.json", time.Now().Format("2006-01-02T15-04-05"))
		}

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var result map[string]any
		if err := c.Create("/api/admin/transfer/export/json", map[string]any{}, &result); err != nil {
			return fmt.Errorf("export failed: %w", err)
		}

		data, err := json.MarshalIndent(result, "", "  ")
		if err != nil {
			return fmt.Errorf("failed to encode export: %w", err)
		}

		if err := os.WriteFile(outFile, data, 0644); err != nil {
			return fmt.Errorf("failed to write file: %w", err)
		}

		fmt.Printf("Exported to %s\n", outFile)
		return nil
	},
}

var transferImportCmd = &cobra.Command{
	Use:   "import <file>",
	Short: "Import configuration from a JSON file",
	Long: `Import Magnet AI resources from a previously exported JSON file.

Example:
  magnet transfer import backup.json
  magnet transfer import backup.json --dry-run`,
	Args: cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		dryRun, _ := cmd.Flags().GetBool("dry-run")

		cfg, err := config.Load()
		if err != nil {
			return err
		}

		data, err := os.ReadFile(args[0])
		if err != nil {
			return fmt.Errorf("cannot read file: %w", err)
		}

		if dryRun {
			fmt.Printf("Dry run: would import %d bytes from %s\n", len(data), args[0])
			return nil
		}

		var body map[string]any
		if err := json.Unmarshal(data, &body); err != nil {
			return fmt.Errorf("invalid JSON file: %w", err)
		}

		c := client.New(cfg)
		var result map[string]any
		if err := c.Create("/api/admin/transfer/import/json", body, &result); err != nil {
			return fmt.Errorf("import failed: %w", err)
		}

		fmt.Printf("Import completed successfully from %s\n", args[0])
		if summary, ok := result["summary"]; ok {
			fmt.Printf("Summary: %v\n", summary)
		}
		return nil
	},
}

func init() {
	transferExportCmd.Flags().StringP("output", "o", "", "Output file path (default: magnet-export-<timestamp>.json)")
	transferImportCmd.Flags().Bool("dry-run", false, "Show what would be imported without making changes")

	transferCmd.AddCommand(transferExportCmd, transferImportCmd)
	rootCmd.AddCommand(transferCmd)
}
