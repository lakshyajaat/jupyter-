package config

import (
	"log"

	"github.com/spf13/viper"
)

type Config struct {
	Server struct {
		Port int
	}
	Database struct {
		Host     string
		Port     int
		User     string
		Password string
		Name     string
	}
}

func Load() *Config {
	v := viper.New()
	v.SetConfigType("yaml")
	v.SetConfigFile("configs/config.yaml")

	if err := v.ReadInConfig(); err != nil {
		log.Fatalf("config error: %v", err)
	}

	var cfg Config
	v.Unmarshal(&cfg)
	return &cfg
}
