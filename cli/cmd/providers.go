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

var providersCmd = &cobra.Command{
	Use:   "providers",
	Short: "Manage AI providers",
}

var providersListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all providers",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var result struct {
			Items []struct {
				ID           string `json:"id"`
				Name         string `json:"name"`
				ProviderType string `json:"provider_type"`
				IsActive     bool   `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/providers", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "TYPE", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, a.ProviderType, boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var providersGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get provider by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/providers/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var providersCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create provider from YAML/JSON file",
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
		if err := c.Create("/api/admin/providers", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var providersUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update provider from YAML/JSON file",
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
		if err := c.Update("/api/admin/providers/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var providersDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete provider by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/providers/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	providersCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	providersCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	providersUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	providersUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	providersCmd.AddCommand(providersListCmd, providersGetCmd, providersCreateCmd, providersUpdateCmd, providersDeleteCmd)
	rootCmd.AddCommand(providersCmd)
}
