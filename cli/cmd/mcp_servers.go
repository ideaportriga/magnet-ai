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

var mcpCmd = &cobra.Command{
	Use:     "mcp",
	Aliases: []string{"mcp-servers"},
	Short:   "Manage MCP servers",
}

var mcpListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all MCP servers",
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
				ServerType  string  `json:"server_type"`
				Description *string `json:"description"`
				IsActive    bool    `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/mcp_servers", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "TYPE", "DESCRIPTION", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, a.ServerType, truncate(strVal(a.Description), 40), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var mcpGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get MCP server by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/mcp_servers/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var mcpCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create MCP server from YAML/JSON file",
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
		if err := c.Create("/api/admin/mcp_servers", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var mcpUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update MCP server from YAML/JSON file",
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
		if err := c.Update("/api/admin/mcp_servers/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var mcpDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete MCP server by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/mcp_servers/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	mcpCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	mcpCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	mcpUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	mcpUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	mcpCmd.AddCommand(mcpListCmd, mcpGetCmd, mcpCreateCmd, mcpUpdateCmd, mcpDeleteCmd)
	rootCmd.AddCommand(mcpCmd)
}
