// Package config holds the agent's settings, read from defaults, the file named by --config and environment
// variables prefixed AGENT_.
package config

import (
	"errors"
	"fmt"
	"net/url"

	base "github.com/to-be-named-1/to-be-named/internal/config"
	"github.com/to-be-named-1/to-be-named/internal/logging"
)

const EnvPrefix = "AGENT_"

type Config struct {
	Log          logging.Settings `yaml:"log" envPrefix:"LOG_"`
	ControlPlane ControlPlane     `yaml:"control_plane" envPrefix:"CONTROL_PLANE_"`
}

type ControlPlane struct {
	// URL is the control plane's address, which the agent always calls outward over HTTPS.
	URL string `yaml:"url" env:"URL"`
}

func Defaults() Config {
	return Config{Log: logging.DefaultSettings()}
}

func Load(path string) (Config, error) {
	cfg := Defaults()
	err := base.Load(&cfg, base.Options{Path: path, Prefix: EnvPrefix})
	return cfg, err
}

func (c *Config) Validate() error {
	errs := []error{c.Log.Validate()}
	if c.ControlPlane.URL == "" {
		errs = append(errs, errors.New("control_plane.url: required"))
	} else if u, err := url.Parse(c.ControlPlane.URL); err != nil || u.Scheme != "https" || u.Host == "" {
		errs = append(errs, fmt.Errorf("control_plane.url: %q is not an https URL", c.ControlPlane.URL))
	}
	return errors.Join(errs...)
}
