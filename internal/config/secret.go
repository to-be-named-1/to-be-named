package config

import (
	"log/slog"
)

const redacted = "[redacted]"

// Secret holds a sensitive setting, such as a password or a connection string with credentials. It prints,
// logs and marshals as "[redacted]"; only Reveal returns its value.
//
// A Secret is never read from the configuration file. It comes from its environment variable, or from the file
// whose path is given in the variable of the same name suffixed _FILE.
type Secret struct {
	value string
}

// NewSecret returns a Secret holding value.
func NewSecret(value string) Secret {
	return Secret{value: value}
}

// Reveal returns the secret's value.
func (s Secret) Reveal() string {
	return s.value
}

// IsZero reports whether the secret is empty.
func (s Secret) IsZero() bool {
	return s.value == ""
}

// String returns "[redacted]".
func (Secret) String() string {
	return redacted
}

// GoString returns "[redacted]", so that %#v does not print the value either.
func (Secret) GoString() string {
	return redacted
}

// LogValue returns "[redacted]".
func (Secret) LogValue() slog.Value {
	return slog.StringValue(redacted)
}

// MarshalText returns "[redacted]", which JSON and YAML encoders use.
func (Secret) MarshalText() ([]byte, error) {
	return []byte(redacted), nil
}

// UnmarshalText sets the secret's value; the environment reader uses it.
func (s *Secret) UnmarshalText(text []byte) error {
	s.value = string(text)
	return nil
}
