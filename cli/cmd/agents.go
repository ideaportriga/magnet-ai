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
				ID          string  `json:"id" yaml:"id"`
				Name        string  `json:"name" yaml:"name"`
				Description *string `json:"description" yaml:"description"`
				IsActive    bool    `json:"is_active" yaml:"is_active"`
			} `json:"items" yaml:"items"`
		}
		if err := c.List("/api/admin/agents", map[string]string{"page_size": "200"}, &result); err != nil {
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
		return output.Print(output.Format(outputFormat()), nil, nil, result)
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
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var agentsUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update agent from YAML/JSON file",
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
		if err := c.Update("/api/admin/agents/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var agentsDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete agent by ID",
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
	agentsCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	agentsUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	agentsUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	agentsCmd.AddCommand(agentsListCmd, agentsGetCmd, agentsCreateCmd, agentsUpdateCmd, agentsDeleteCmd)
	rootCmd.AddCommand(agentsCmd)
}
