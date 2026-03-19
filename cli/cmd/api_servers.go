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

var apiServersCmd = &cobra.Command{
	Use:   "api-servers",
	Short: "Manage API servers",
}

var apiServersListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all API servers",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var result struct {
			Items []struct {
				ID          string  `json:"id"`
				Name        string  `json:"name"`
				Description *string `json:"description"`
				IsActive    bool    `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/api_servers", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "DESCRIPTION", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, truncate(strVal(a.Description), 50), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var apiServersGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get API server by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/api_servers/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiServersCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create API server from YAML/JSON file",
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
		if err := c.Create("/api/admin/api_servers", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiServersUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update API server from YAML/JSON file",
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
		if err := c.Update("/api/admin/api_servers/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var apiServersDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete API server by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/api_servers/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	apiServersCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	apiServersCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	apiServersUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	apiServersUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	apiServersCmd.AddCommand(apiServersListCmd, apiServersGetCmd, apiServersCreateCmd, apiServersUpdateCmd, apiServersDeleteCmd)
	rootCmd.AddCommand(apiServersCmd)
}
