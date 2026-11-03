package logging

import (
	"bytes"
	"context"
	"encoding/json"
	"log/slog"
	"strings"
	"testing"

	"github.com/google/go-cmp/cmp"
)

func TestJSONLine(t *testing.T) {
	var out bytes.Buffer
	logger, err := New(&out, DefaultSettings())
	if err != nil {
		t.Fatal(err)
	}
	ctx := WithAttrs(context.Background(), slog.String(KeyTenantID, "t1"))
	ctx = WithAttrs(ctx, slog.String(KeyRunID, "r1"))
	logger.InfoContext(ctx, "run started", "nodes", 3)

	line := out.String()
	if !strings.HasPrefix(line, `{"time":`) || !strings.Contains(line, `,"level":"INFO","msg":"run started",`) {
		t.Errorf("unexpected key order: %s", line)
	}
	var got map[string]any
	if err := json.Unmarshal([]byte(line), &got); err != nil {
		t.Fatal(err)
	}
	delete(got, "time")
	want := map[string]any{"level": "INFO", "msg": "run started", "nodes": 3.0, "tenant_id": "t1", "run_id": "r1"}
	if diff := cmp.Diff(want, got); diff != "" {
		t.Errorf("line (-want +got):\n%s", diff)
	}
}

func TestLevelFilters(t *testing.T) {
	var out bytes.Buffer
	logger, err := New(&out, Settings{Level: LevelWarn, Format: FormatJSON})
	if err != nil {
		t.Fatal(err)
	}
	logger.Info("dropped")
	logger.Warn("kept")
	if strings.Contains(out.String(), "dropped") || !strings.Contains(out.String(), "kept") {
		t.Errorf("output: %s", out.String())
	}
}

func TestTextFormat(t *testing.T) {
	var out bytes.Buffer
	logger, err := New(&out, Settings{Level: LevelInfo, Format: FormatText})
	if err != nil {
		t.Fatal(err)
	}
	logger.InfoContext(WithAttrs(context.Background(), slog.String(KeyAttemptID, "a1")), "hello")
	if !strings.Contains(out.String(), "msg=hello") || !strings.Contains(out.String(), "attempt_id=a1") {
		t.Errorf("output: %s", out.String())
	}
}

func TestAttrsSurviveWith(t *testing.T) {
	var out bytes.Buffer
	logger, err := New(&out, DefaultSettings())
	if err != nil {
		t.Fatal(err)
	}
	logger.With("component", "scheduler").InfoContext(WithAttrs(context.Background(), slog.String(KeyRequestID, "q1")), "tick")
	if !strings.Contains(out.String(), `"component":"scheduler"`) || !strings.Contains(out.String(), `"request_id":"q1"`) {
		t.Errorf("output: %s", out.String())
	}
}

func TestInvalidSettings(t *testing.T) {
	err := Settings{Level: "loud", Format: "xml"}.Validate()
	if err == nil || !strings.Contains(err.Error(), "log.level") || !strings.Contains(err.Error(), "log.format") {
		t.Errorf("want both settings reported, got %v", err)
	}
	if _, err := New(&bytes.Buffer{}, Settings{Level: "loud", Format: FormatJSON}); err == nil {
		t.Error("New accepted an invalid level")
	}
}
