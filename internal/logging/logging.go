// Package logging builds the structured loggers of the platform's Go processes: log/slog writing one JSON
// object per line, or text, with the attributes of the current request or attempt added from its context.
package logging

import (
	"context"
	"errors"
	"fmt"
	"io"
	"log/slog"
	"strings"
)

// Formats of log output.
const (
	FormatJSON = "json"
	FormatText = "text"
)

const (
	LevelDebug = "debug"
	LevelInfo  = "info"
	LevelWarn  = "warn"
	LevelError = "error"
)

// Keys of the attributes that identify what a line was written for.
const (
	KeyTenantID  = "tenant_id"
	KeyProjectID = "project_id"
	KeyRunID     = "run_id"
	KeyAttemptID = "attempt_id"
	KeyRequestID = "request_id"
)

type Settings struct {
	Level  string `yaml:"level" env:"LEVEL"`
	Format string `yaml:"format" env:"FORMAT"`
}

func DefaultSettings() Settings {
	return Settings{Level: "info", Format: FormatJSON}
}

// Validate reports an unknown level or format.
func (s Settings) Validate() error {
	var errs []error
	if _, err := parseLevel(s.Level); err != nil {
		errs = append(errs, err)
	}
	if s.Format != FormatJSON && s.Format != FormatText {
		errs = append(errs, fmt.Errorf("log.format: %q is not json or text", s.Format))
	}
	return errors.Join(errs...)
}

func parseLevel(name string) (slog.Level, error) {
	switch strings.ToLower(name) {
	case LevelDebug:
		return slog.LevelDebug, nil
	case LevelInfo:
		return slog.LevelInfo, nil
	case LevelWarn:
		return slog.LevelWarn, nil
	case LevelError:
		return slog.LevelError, nil
	}
	return 0, fmt.Errorf("log.level: %q is not debug, info, warn or error", name)
}

// New returns a logger writing to w as settings say, which must be valid. Processes write to standard error.
func New(w io.Writer, settings Settings) (*slog.Logger, error) {
	if err := settings.Validate(); err != nil {
		return nil, err
	}
	level, _ := parseLevel(settings.Level)
	opts := &slog.HandlerOptions{Level: level}
	var handler slog.Handler
	if settings.Format == FormatText {
		handler = slog.NewTextHandler(w, opts)
	} else {
		handler = slog.NewJSONHandler(w, opts)
	}
	return slog.New(contextHandler{handler}), nil
}

type contextKey struct{}

// WithAttrs returns a context whose log lines carry attrs, after any the context already carries.
func WithAttrs(ctx context.Context, attrs ...slog.Attr) context.Context {
	existing, _ := ctx.Value(contextKey{}).([]slog.Attr)
	merged := make([]slog.Attr, 0, len(existing)+len(attrs))
	merged = append(merged, existing...)
	merged = append(merged, attrs...)
	return context.WithValue(ctx, contextKey{}, merged)
}

// contextHandler adds the attributes of WithAttrs to each record.
type contextHandler struct {
	slog.Handler
}

func (h contextHandler) Handle(ctx context.Context, r slog.Record) error {
	if attrs, ok := ctx.Value(contextKey{}).([]slog.Attr); ok {
		r.AddAttrs(attrs...)
	}
	return h.Handler.Handle(ctx, r)
}

func (h contextHandler) WithAttrs(attrs []slog.Attr) slog.Handler {
	return contextHandler{h.Handler.WithAttrs(attrs)}
}

func (h contextHandler) WithGroup(name string) slog.Handler {
	return contextHandler{h.Handler.WithGroup(name)}
}
