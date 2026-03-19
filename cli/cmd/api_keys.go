package cmd

import (
	"fmt"
	"os"

	"magnet-ai/cli/internal/client"
	"magnet-ai/cli/internal/config"
	"magnet-ai/cli/internal/output"

	"github.com/spf13/cobra"
	"gopkg.in/yaml.v3"
)

var apiKeysCmd = &cobra.Command{
	Use:     "api-keys",
	Aliases: []string{"keys"},
	Short:   "Manage API keys",
}

var apiKeysListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all API keys",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var result struct {
			Items []struct {
				ID       string  `json:"id"`
				Name     string  `json:"name"`
				KeyHint  *string `json:"key_hint"`
				IsActive bool    `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/api_keys", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "KEY HINT", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, strVal(a.KeyHint), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var apiKeysGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get API key by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/api_keys/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiKeysCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create API key from YAML/JSON file",
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
		if err := c.Create("/api/admin/api_keys", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiKeysUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update API key from YAML/JSON file",
	Args:  cobra.ExactArgs(1),
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
		if err := c.Update("/api/admin/api_keys/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiKeysDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete API key by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/api_keys/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	apiKeysCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	apiKeysCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	apiKeysUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	apiKeysUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	apiKeysCmd.AddCommand(apiKeysListCmd, apiKeysGetCmd, apiKeysCreateCmd, apiKeysUpdateCmd, apiKeysDeleteCmd)
	rootCmd.AddCommand(apiKeysCmd)
}
