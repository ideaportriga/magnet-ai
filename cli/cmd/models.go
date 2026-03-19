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

var modelsCmd = &cobra.Command{
	Use:     "models",
	Aliases: []string{"ai-models"},
	Short:   "Manage AI models",
}

var modelsListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all AI models",
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		var result struct {
			Items []struct {
				ID         string  `json:"id"`
				Name       string  `json:"name"`
				ModelName  string  `json:"model_name"`
				ProviderID *string `json:"provider_id"`
				IsActive   bool    `json:"is_active"`
			} `json:"items"`
		}
		if err := c.List("/api/admin/models", map[string]string{"page_size": "200"}, &result); err != nil {
			return err
		}

		fmt := output.Format(outputFormat())
		if fmt != output.FormatTable {
			return output.Print(fmt, nil, nil, result.Items)
		}
		headers := []string{"ID", "NAME", "MODEL NAME", "PROVIDER ID", "ACTIVE"}
		rows := make([][]string, len(result.Items))
		for i, a := range result.Items {
			rows[i] = []string{a.ID, a.Name, a.ModelName, strVal(a.ProviderID), boolStr(a.IsActive)}
		}
		return output.Print(fmt, headers, rows, nil)
	},
}

var modelsGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get AI model by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/models/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var modelsCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create AI model from YAML/JSON file",
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
		if err := c.Create("/api/admin/models", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var modelsUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update AI model from YAML/JSON file",
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
		if err := c.Update("/api/admin/models/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var modelsDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete AI model by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/models/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

func init() {
	modelsCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	modelsCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	modelsUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	modelsUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	modelsCmd.AddCommand(modelsListCmd, modelsGetCmd, modelsCreateCmd, modelsUpdateCmd, modelsDeleteCmd)
	rootCmd.AddCommand(modelsCmd)
}
