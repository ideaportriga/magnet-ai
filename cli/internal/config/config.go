package config

import (
	"fmt"
	"os"
	"path/filepath"

	"github.com/spf13/viper"
)

type Config struct {
	BaseURL string `mapstructure:"base_url"`
	APIKey  string `mapstructure:"api_key"`
	Output  string `mapstructure:"output"` // table|json|yaml
}

func Load() (*Config, error) {
	viper.SetEnvPrefix("MAGNET")
	viper.AutomaticEnv()

	// ~/.magnet/config.yaml
	home, _ := os.UserHomeDir()
	viper.AddConfigPath(filepath.Join(home, ".magnet"))
	viper.SetConfigName("config")
	viper.SetConfigType("yaml")
	_ = viper.ReadInConfig()

	viper.BindEnv("base_url", "MAGNET_BASE_URL")  //nolint:errcheck
	viper.BindEnv("api_key", "MAGNET_API_KEY")     //nolint:errcheck

	viper.SetDefault("base_url", "http://localhost:8000")
	viper.SetDefault("output", "table")

	var cfg Config
	if err := viper.Unmarshal(&cfg); err != nil {
		return nil, fmt.Errorf("config error: %w", err)
	}
	if cfg.APIKey == "" {
		return nil, fmt.Errorf("API key is not set (use --api-key flag or MAGNET_API_KEY env var)")
	}
	return &cfg, nil
}
