// Package config holds the control plane's settings, read from defaults, the file named by --config and
// environment variables prefixed CONTROLPLANE_.
package config

import (
	"errors"
	"fmt"
	"slices"

	base "github.com/to-be-named-1/to-be-named/internal/config"
	"github.com/to-be-named-1/to-be-named/internal/logging"
)

const EnvPrefix = "CONTROLPLANE_"

// Roles a process may be configured with. The leader role is held by the elected candidate and never
// configured.
const (
	RoleAll       = "all"
	RoleAPI       = "api"
	RoleWorker    = "worker"
	RoleCandidate = "candidate"
)

var configurableRoles = []string{RoleAll, RoleAPI, RoleWorker, RoleCandidate}

type Config struct {
	Log      logging.Settings `yaml:"log" envPrefix:"LOG_"`
	Roles    []string         `yaml:"roles" env:"ROLES"`
	Database Database         `yaml:"database" envPrefix:"DATABASE_"`
}

type Database struct {
	URL base.Secret `yaml:"-" env:"URL"`
}

// Defaults returns the settings before any file or variable is read: one process with every role.
func Defaults() Config {
	return Config{
		Log:   logging.DefaultSettings(),
		Roles: []string{RoleAll},
	}
}

// Load returns the settings read from the file at path, empty for none, and the process environment.
func Load(path string) (Config, error) {
	cfg := Defaults()
	err := base.Load(&cfg, base.Options{Path: path, Prefix: EnvPrefix})
	return cfg, err
}

// Validate reports every invalid setting.
func (c *Config) Validate() error {
	errs := []error{c.Log.Validate()}
	if len(c.Roles) == 0 {
		errs = append(errs, errors.New("roles: at least one role is required"))
	}
	for _, role := range c.Roles {
		if !slices.Contains(configurableRoles, role) {
			errs = append(errs, fmt.Errorf("roles: %q is not one of %v", role, configurableRoles))
		}
	}
	if c.Database.URL.IsZero() {
		errs = append(errs, fmt.Errorf("database.url: required; set %sDATABASE_URL or %sDATABASE_URL_FILE", EnvPrefix, EnvPrefix))
	}
	return errors.Join(errs...)
}
