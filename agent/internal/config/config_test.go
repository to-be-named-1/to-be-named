package config

import (
	"strings"
	"testing"

	base "github.com/to-be-named-1/to-be-named/internal/config"
)

func TestNames(t *testing.T) {
	if err := base.CheckNames(Config{}); err != nil {
		t.Error(err)
	}
}

func TestControlPlaneURL(t *testing.T) {
	for _, tc := range []struct {
		url     string
		problem string
	}{
		{"https://cp.example.com", ""},
		{"", "required"},
		{"http://cp.example.com", "not an https URL"},
		{"cp.example.com", "not an https URL"},
	} {
		cfg := Defaults()
		err := base.Load(&cfg, base.Options{Prefix: EnvPrefix, Environment: map[string]string{"AGENT_CONTROL_PLANE_URL": tc.url}})
		switch {
		case tc.problem == "" && err != nil:
			t.Errorf("%q: %v", tc.url, err)
		case tc.problem != "" && (err == nil || !strings.Contains(err.Error(), tc.problem)):
			t.Errorf("%q: want %q, got %v", tc.url, tc.problem, err)
		}
	}
}
