package config

import (
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"

	base "github.com/to-be-named-1/to-be-named/internal/config"
)

func load(t *testing.T, file string, environment map[string]string) (Config, error) {
	t.Helper()
	var path string
	if file != "" {
		path = filepath.Join(t.TempDir(), "controlplane.yaml")
		if err := os.WriteFile(path, []byte(file), 0o600); err != nil {
			t.Fatal(err)
		}
	}
	cfg := Defaults()
	err := base.Load(&cfg, base.Options{Path: path, Prefix: EnvPrefix, Environment: environment})
	return cfg, err
}

func TestNames(t *testing.T) {
	if err := base.CheckNames(Config{}); err != nil {
		t.Error(err)
	}
}

func TestDefaultsNeedOnlyTheDatabase(t *testing.T) {
	cfg, err := load(t, "", map[string]string{"CONTROLPLANE_DATABASE_URL": "postgres://cp:pw@db/cp"})
	if err != nil {
		t.Fatal(err)
	}
	if diff := cmp.Diff([]string{RoleAll}, cfg.Roles); diff != "" {
		t.Errorf("roles (-want +got):\n%s", diff)
	}
	if cfg.Log.Level != "info" || cfg.Log.Format != "json" {
		t.Errorf("log = %+v", cfg.Log)
	}
}

func TestFileAndEnvironment(t *testing.T) {
	cfg, err := load(t, "log:\n  format: text\nroles: [api, worker]\n", map[string]string{
		"CONTROLPLANE_DATABASE_URL": "postgres://cp:pw@db/cp",
		"CONTROLPLANE_LOG_LEVEL":    "debug",
	})
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Log.Format != "text" || cfg.Log.Level != "debug" {
		t.Errorf("log = %+v", cfg.Log)
	}
	if diff := cmp.Diff([]string{RoleAPI, RoleWorker}, cfg.Roles); diff != "" {
		t.Errorf("roles (-want +got):\n%s", diff)
	}
}

func TestPartialFileKeepsNestedDefaults(t *testing.T) {
	cfg, err := load(t, "log:\n  format: text\n", map[string]string{"CONTROLPLANE_DATABASE_URL": "postgres://cp:pw@db/cp"})
	if err != nil {
		t.Fatal(err)
	}
	if cfg.Log.Format != "text" || cfg.Log.Level != "info" {
		t.Errorf("log = %+v, want format text with the default level info", cfg.Log)
	}
}

func TestInvalid(t *testing.T) {
	_, err := load(t, "roles: [leader]\n", map[string]string{"CONTROLPLANE_LOG_FORMAT": "xml"})
	for _, want := range []string{`"leader"`, "log.format", "CONTROLPLANE_DATABASE_URL"} {
		if err == nil || !strings.Contains(err.Error(), want) {
			t.Errorf("error %v does not mention %s", err, want)
		}
	}
}
