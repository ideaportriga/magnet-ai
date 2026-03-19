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

var appsCmd = &cobra.Command{
	Use:     "apps",
	Aliases: []string{"ai-apps"},
	Short:   "Manage AI apps",
}

var appsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all AI apps",
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
				AppType  string  `json:"app_type"`
				IsActive bool    `json:"is_active"`
				AgentID  *string `json:"agent_id"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/ai_apps", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "TYPE", "AGENT ID", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, a.AppType, strVal(a.AgentID), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var appsGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get AI app by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/ai_apps/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var appsCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create AI app from YAML/JSON file",
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
		if err := c.Create("/api/admin/ai_apps", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var appsUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update AI app from YAML/JSON file",
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
		if err := c.Update("/api/admin/ai_apps/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var appsDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete AI app by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/ai_apps/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	appsCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	appsCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	appsUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	appsUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	appsCmd.AddCommand(appsListCmd, appsGetCmd, appsCreateCmd, appsUpdateCmd, appsDeleteCmd)
	rootCmd.AddCommand(appsCmd)
}
