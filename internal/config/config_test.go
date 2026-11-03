package config

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

type testSettings struct {
	Level    string       `yaml:"level" env:"LEVEL"`
	Workers  int          `yaml:"workers" env:"WORKERS"`
	Tags     []string     `yaml:"tags" env:"TAGS"`
	Database testDatabase `yaml:"database" envPrefix:"DATABASE_"`
	failure  error
}

type testDatabase struct {
	Host     string `yaml:"host" env:"HOST"`
	Password Secret `yaml:"-" env:"PASSWORD"`
}

func (s *testSettings) Validate() error { return s.failure }

func defaults() testSettings {
	return testSettings{Level: "info", Workers: 1, Database: testDatabase{Host: "localhost"}}
}

func writeFile(t *testing.T, name, content string) string {
	t.Helper()
	path := filepath.Join(t.TempDir(), name)
	if err := os.WriteFile(path, []byte(content), 0o600); err != nil {
		t.Fatal(err)
	}
	return path
}

func TestPrecedence(t *testing.T) {
	path := writeFile(t, "config.yaml", "level: debug\nworkers: 4\ndatabase:\n  host: db.internal\n")
	s := defaults()
	err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{"APP_WORKERS": "8"}})
	if err != nil {
		t.Fatal(err)
	}
	got := map[string]any{"level": s.Level, "workers": s.Workers, "host": s.Database.Host}
	want := map[string]any{"level": "debug", "workers": 8, "host": "db.internal"}
	if diff := cmp.Diff(want, got); diff != "" {
		t.Errorf("settings (-want +got):\n%s", diff)
	}
}

func TestPartialFileKeepsNestedDefaults(t *testing.T) {
	path := writeFile(t, "config.yaml", "database:\n  password_hint: none\n")
	s := defaults()
	err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{}})
	if err == nil {
		t.Fatal("unknown nested key accepted")
	}
	path = writeFile(t, "config.yaml", "level: debug\n")
	s = defaults()
	if err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{}}); err != nil {
		t.Fatal(err)
	}
	if s.Database.Host != "localhost" || s.Workers != 1 {
		t.Errorf("defaults outside the file were reset: %+v", s)
	}
}

func TestDefaultsWithoutFileOrEnvironment(t *testing.T) {
	s := defaults()
	if err := Load(&s, Options{Prefix: "APP_", Environment: map[string]string{}}); err != nil {
		t.Fatal(err)
	}
	if s.Level != "info" || s.Workers != 1 || s.Database.Host != "localhost" {
		t.Errorf("defaults changed: %+v", s)
	}
}

func TestListFromEnvironment(t *testing.T) {
	s := defaults()
	if err := Load(&s, Options{Prefix: "APP_", Environment: map[string]string{"APP_TAGS": "a,b"}}); err != nil {
		t.Fatal(err)
	}
	if diff := cmp.Diff([]string{"a", "b"}, s.Tags); diff != "" {
		t.Errorf("tags (-want +got):\n%s", diff)
	}
}

func TestUnknownKeyInFile(t *testing.T) {
	path := writeFile(t, "config.yaml", "level: debug\nwokers: 4\n")
	s := defaults()
	err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{}})
	if err == nil || !strings.Contains(err.Error(), "wokers") {
		t.Fatalf("want an error naming the unknown key, got %v", err)
	}
}

func TestSecretNotReadFromFile(t *testing.T) {
	path := writeFile(t, "config.yaml", "database:\n  password: hunter2\n")
	s := defaults()
	err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{}})
	if err == nil || !strings.Contains(err.Error(), "password") {
		t.Fatalf("want an error naming the secret's key, got %v", err)
	}
	if !s.Database.Password.IsZero() {
		t.Error("the secret was read from the file")
	}
}

func TestSecretFromEnvironment(t *testing.T) {
	s := defaults()
	if err := Load(&s, Options{Prefix: "APP_", Environment: map[string]string{"APP_DATABASE_PASSWORD": "hunter2"}}); err != nil {
		t.Fatal(err)
	}
	if got := s.Database.Password.Reveal(); got != "hunter2" {
		t.Errorf("secret = %q, want hunter2", got)
	}
}

func TestSecretFromFile(t *testing.T) {
	path := writeFile(t, "password", "hunter2\n")
	s := defaults()
	if err := Load(&s, Options{Prefix: "APP_", Environment: map[string]string{"APP_DATABASE_PASSWORD_FILE": path}}); err != nil {
		t.Fatal(err)
	}
	if got := s.Database.Password.Reveal(); got != "hunter2" {
		t.Errorf("secret = %q, want hunter2 without the trailing newline", got)
	}
}

func TestSecretSetTwice(t *testing.T) {
	path := writeFile(t, "password", "hunter2")
	s := defaults()
	err := Load(&s, Options{Prefix: "APP_", Environment: map[string]string{
		"APP_DATABASE_PASSWORD":      "other",
		"APP_DATABASE_PASSWORD_FILE": path,
	}})
	if err == nil || !strings.Contains(err.Error(), "APP_DATABASE_PASSWORD_FILE") {
		t.Fatalf("want an error naming both variables, got %v", err)
	}
}

func TestEveryErrorReported(t *testing.T) {
	path := writeFile(t, "config.yaml", "unknown: 1\n")
	invalid := errors.New("workers: must be positive")
	s := defaults()
	s.failure = invalid
	err := Load(&s, Options{Path: path, Prefix: "APP_", Environment: map[string]string{"APP_WORKERS": "many"}})
	for _, want := range []string{"unknown", "APP_WORKERS", "workers: must be positive"} {
		if err == nil || !strings.Contains(err.Error(), want) {
			t.Errorf("error %v does not mention %q", err, want)
		}
	}
	if !errors.Is(err, invalid) {
		t.Error("the validation error is not wrapped")
	}
}

func TestSecretRedacted(t *testing.T) {
	s := NewSecret("hunter2")
	var logged bytes.Buffer
	slog.New(slog.NewJSONHandler(&logged, nil)).Info("connecting", "password", s)
	marshaled, err := json.Marshal(struct{ Password Secret }{s})
	if err != nil {
		t.Fatal(err)
	}
	for name, text := range map[string]string{
		"%v":   fmt.Sprintf("%v", s),
		"%s":   fmt.Sprintf("password=%s", s),
		"%#v":  fmt.Sprintf("%#v", s),
		"%+v":  fmt.Sprintf("%+v", struct{ P Secret }{s}),
		"slog": logged.String(),
		"json": string(marshaled),
	} {
		if strings.Contains(text, "hunter2") || !strings.Contains(text, redacted) {
			t.Errorf("%s printed %q", name, text)
		}
	}
}

func TestCheckNames(t *testing.T) {
	if err := CheckNames(testSettings{}); err != nil {
		t.Errorf("valid tags rejected: %v", err)
	}
	type broken struct {
		MaxWorkers int `yaml:"max_workers" env:"WORKERS"`
		Nested     struct {
			Host string `yaml:"host" env:"HOST"`
		} `yaml:"nested" envPrefix:"NEST_"`
		Token Secret `yaml:"token" env:"TOKEN"`
	}
	err := CheckNames(broken{})
	for _, want := range []string{`"MAX_WORKERS"`, `"NESTED_"`, "Token"} {
		if err == nil || !strings.Contains(err.Error(), want) {
			t.Errorf("error %v does not mention %s", err, want)
		}
	}
}
