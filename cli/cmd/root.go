package cmd

import (
	"fmt"
	"os"
	"strings"

	"github.com/spf13/cobra"
	"github.com/spf13/viper"
)

var version = "dev"

var rootCmd = &cobra.Command{
	Use:   "magnet",
	Short: "Magnet AI CLI",
	Long: `Magnet AI CLI — manage agents, knowledge graphs, collections,
providers, models, and more from the command line.

Configuration:
  Set MAGNET_API_KEY and MAGNET_BASE_URL environment variables,
  or create ~/.magnet/config.yaml with base_url and api_key fields.`,
	Version: version,
}

func Execute() {
	if err := rootCmd.Execute(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func init() {
	rootCmd.PersistentFlags().String("output", "table", "Output format: table|json|yaml")
	rootCmd.PersistentFlags().String("api-key", "", "API key (overrides MAGNET_API_KEY)")
	rootCmd.PersistentFlags().String("base-url", "", "Base URL (overrides MAGNET_BASE_URL)")

	viper.BindPFlag("output", rootCmd.PersistentFlags().Lookup("output"))     //nolint:errcheck
	viper.BindPFlag("api_key", rootCmd.PersistentFlags().Lookup("api-key"))   //nolint:errcheck
	viper.BindPFlag("base_url", rootCmd.PersistentFlags().Lookup("base-url")) //nolint:errcheck
}

// helpers shared across commands

func truncate(s string, n int) string {
	s = strings.ReplaceAll(s, "\n", " ")
	if len(s) > n {
		return s[:n] + "..."
	}
	return s
}

func boolStr(b bool) string {
	if b {
		return "yes"
	}
	return "no"
}

func strVal(p *string) string {
	if p == nil {
		return ""
	}
	return *p
}

func outputFormat() string {
	return viper.GetString("output")
}
