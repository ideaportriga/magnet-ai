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

var kgCmd = &cobra.Command{
	Use:     "kg",
	Aliases: []string{"knowledge-graphs"},
	Short:   "Manage knowledge graphs",
}

var kgListCmd = &cobra.Command{
	Use:   "list",
	Short: "List all knowledge graphs",
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
		if err := c.List("/api/admin/knowledge_graphs", map[string]string{"page_size": "200"}, &result); err != nil {
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

var kgGetCmd = &cobra.Command{
	Use:   "get <id>",
	Short: "Get knowledge graph by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		var result map[string]any
		if err := c.Get("/api/admin/knowledge_graphs/"+args[0], &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var kgCreateCmd = &cobra.Command{
	Use:   "create",
	Short: "Create knowledge graph from YAML/JSON file",
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
		if err := c.Create("/api/admin/knowledge_graphs", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var kgUpdateCmd = &cobra.Command{
	Use:   "update <id>",
	Short: "Update knowledge graph from YAML/JSON file",
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
		if err := c.Update("/api/admin/knowledge_graphs/"+args[0], body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

var kgDeleteCmd = &cobra.Command{
	Use:   "delete <id>",
	Short: "Delete knowledge graph by ID",
	Args:  cobra.ExactArgs(1),
	RunE: func(cmd *cobra.Command, args []string) error {
		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)
		if err := c.Delete("/api/admin/knowledge_graphs/" + args[0]); err != nil {
			return err
		}
		fmt.Println("Deleted:", args[0])
		return nil
	},
}

var kgSearchCmd = &cobra.Command{
	Use:   "search <id> <query>",
	Short: "Search within a knowledge graph",
	Args:  cobra.ExactArgs(2),
	RunE: func(cmd *cobra.Command, args []string) error {
		kgID := args[0]
		query := args[1]
		topK, _ := cmd.Flags().GetInt("top-k")
		threshold, _ := cmd.Flags().GetFloat64("threshold")

		cfg, err := config.Load()
		if err != nil {
			return err
		}
		c := client.New(cfg)

		body := map[string]any{
			"query":     query,
			"limit":     topK,
			"min_score": threshold,
		}
		var result map[string]any
		if err := c.Create("/api/user/knowledge_graph/"+kgID+"/chunks/search", body, &result); err != nil {
			return err
		}
		return output.Print(output.Format(outputFormat()), nil, nil, result)
	},
}

func init() {
	kgCreateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	kgCreateCmd.MarkFlagRequired("file") //nolint:errcheck

	kgUpdateCmd.Flags().StringP("file", "f", "", "Path to YAML/JSON file (required)")
	kgUpdateCmd.MarkFlagRequired("file") //nolint:errcheck

	kgSearchCmd.Flags().Int("top-k", 5, "Number of results to return")
	kgSearchCmd.Flags().Float64("threshold", 0.0, "Similarity threshold (0.0–1.0)")

	kgCmd.AddCommand(kgListCmd, kgGetCmd, kgCreateCmd, kgUpdateCmd, kgDeleteCmd, kgSearchCmd)
	rootCmd.AddCommand(kgCmd)
}
