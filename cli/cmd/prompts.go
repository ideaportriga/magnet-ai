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

var promptsCmd = &cobra.Command{
	Use:   "prompts",
	Short: "Manage prompts",
}

var promptsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all prompts",
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
				Category *string `json:"category"`
				IsActive bool    `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/prompt_templates", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "CATEGORY", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, strVal(a.Category), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var promptsGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get prompt by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/prompt_templates/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var promptsCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create prompt from YAML/JSON file",
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
		if err := c.Create("/api/admin/prompt_templates", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var promptsUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update prompt from YAML/JSON file",
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
		if err := c.Update("/api/admin/prompt_templates/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var promptsDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete prompt by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/prompt_templates/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	promptsCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	promptsCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	promptsUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	promptsUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	promptsCmd.AddCommand(promptsListCmd, promptsGetCmd, promptsCreateCmd, promptsUpdateCmd, promptsDeleteCmd)
	rootCmd.AddCommand(promptsCmd)
}
