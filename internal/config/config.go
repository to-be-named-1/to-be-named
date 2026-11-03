// Package config loads the settings of the platform's Go processes. Settings start from defaults set in code,
// then an optional YAML file overrides them, then environment variables override both. The file is read
// strictly, secrets come only from the environment, and every invalid setting is reported at once.
//
// A process describes its settings as one struct whose fields carry two tags: `yaml` with the snake_case key,
// and `env` with the same key in upper case, or `envPrefix` with the key in upper case followed by an
// underscore for a nested struct. A field of type [Secret] is tagged `yaml:"-"`. [CheckNames] verifies these
// rules, so that every environment variable's name is derived from its key.
package config

import (
	"errors"
	"fmt"
	"os"
	"reflect"
	"strings"

	"github.com/caarlos0/env/v11"
	"github.com/goccy/go-yaml"
)

// Settings is the struct of a process's settings, holding its defaults when it is loaded.
type Settings interface {
	// Validate reports every invalid setting, joined into one error.
	Validate() error
}

// Options say where settings are loaded from.
type Options struct {
	// Path is the YAML file named by --config; empty when none is given.
	Path string
	// Prefix starts the name of every environment variable, such as "CONTROLPLANE_".
	Prefix string
	// Environment replaces the process environment; nil reads the process environment.
	Environment map[string]string
}

// fileSuffix ends the name of the variable that holds the path of a file containing a secret.
const fileSuffix = "_FILE"

// Load overrides settings, which hold their defaults, with the file and then the environment named by opts, and
// validates the result. It returns every problem it finds, joined into one error.
func Load(settings Settings, opts Options) error {
	environment := opts.Environment
	if environment == nil {
		environment = processEnvironment()
	}

	var errs []error
	if opts.Path != "" {
		if err := loadFile(settings, opts.Path); err != nil {
			errs = append(errs, err)
		}
	}
	if err := env.ParseWithOptions(settings, env.Options{Prefix: opts.Prefix, Environment: environment}); err != nil {
		errs = append(errs, nameVariables(err, settings, opts.Prefix, environment))
	}
	if err := loadSecretFiles(settings, opts.Prefix, environment); err != nil {
		errs = append(errs, err)
	}
	if err := settings.Validate(); err != nil {
		errs = append(errs, err)
	}
	return errors.Join(errs...)
}

func loadFile(settings Settings, path string) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return fmt.Errorf("reading the configuration file: %w", err)
	}
	if err := yaml.UnmarshalWithOptions(data, settings, yaml.Strict()); err != nil {
		return fmt.Errorf("%s: %w", path, err)
	}
	return nil
}

// nameVariables rewrites the environment reader's parse errors, which name Go fields, to name the variable
// that failed instead, which is what an operator sets.
func nameVariables(err error, settings Settings, prefix string, environment map[string]string) error {
	var aggregate env.AggregateError
	if !errors.As(err, &aggregate) {
		return err
	}
	keysByField := map[string][]string{}
	walk(reflect.ValueOf(settings).Elem(), prefix, "", func(f field) {
		if _, set := environment[f.envKey]; f.envKey != "" && set {
			name := f.path[strings.LastIndex(f.path, ".")+1:]
			keysByField[name] = append(keysByField[name], f.envKey)
		}
	})
	errs := make([]error, 0, len(aggregate.Errors))
	for _, e := range aggregate.Errors {
		var parse env.ParseError
		if errors.As(e, &parse) && len(keysByField[parse.Name]) == 1 {
			key := keysByField[parse.Name][0]
			e = fmt.Errorf("%s: %q is not a valid %s: %w", key, environment[key], parse.Type, parse.Err)
		}
		errs = append(errs, e)
	}
	return errors.Join(errs...)
}

// loadSecretFiles reads each secret whose variable suffixed _FILE is set from the file it names.
func loadSecretFiles(settings Settings, prefix string, environment map[string]string) error {
	var errs []error
	walk(reflect.ValueOf(settings).Elem(), prefix, "", func(f field) {
		if !f.secret || f.envKey == "" {
			return
		}
		path, ok := environment[f.envKey+fileSuffix]
		if !ok || path == "" {
			return
		}
		if direct, set := environment[f.envKey]; set && direct != "" {
			errs = append(errs, fmt.Errorf("%s and %s are both set; set one of them", f.envKey, f.envKey+fileSuffix))
			return
		}
		data, err := os.ReadFile(path)
		if err != nil {
			errs = append(errs, fmt.Errorf("%s: reading the secret's file: %w", f.envKey+fileSuffix, err))
			return
		}
		// Files written by editors and by echo end with a newline that is not part of the secret.
		value := strings.TrimSuffix(strings.TrimSuffix(string(data), "\n"), "\r")
		f.value.Set(reflect.ValueOf(NewSecret(value)))
	})
	return errors.Join(errs...)
}

// CheckNames reports every field of settings whose tags break the naming rules of the package documentation.
// Each process's tests call it on its settings struct.
func CheckNames(settings any) error {
	v := reflect.ValueOf(settings)
	if v.Kind() == reflect.Pointer {
		v = v.Elem()
	}
	var errs []error
	walk(v, "", "", func(f field) {
		switch {
		case f.secret && f.yamlKey != "-":
			errs = append(errs, fmt.Errorf("%s: a secret must be tagged yaml:\"-\"", f.path))
		case f.secret && f.envKey == "":
			errs = append(errs, fmt.Errorf("%s: a secret must have an env tag", f.path))
		case !f.secret && f.nested && f.envPrefix != strings.ToUpper(f.yamlKey)+"_":
			errs = append(errs, fmt.Errorf("%s: envPrefix must be %q", f.path, strings.ToUpper(f.yamlKey)+"_"))
		case !f.secret && !f.nested && f.envName != strings.ToUpper(f.yamlKey):
			errs = append(errs, fmt.Errorf("%s: env must be %q", f.path, strings.ToUpper(f.yamlKey)))
		}
	})
	return errors.Join(errs...)
}

// field describes one exported field reached by walk.
type field struct {
	path      string // dotted Go field path, for messages
	yamlKey   string // the yaml tag's key
	envName   string // the env tag's name, without prefixes
	envPrefix string // the envPrefix tag, for a nested struct
	envKey    string // the full environment variable name
	nested    bool
	secret    bool
	value     reflect.Value
}

var secretType = reflect.TypeFor[Secret]()

// walk calls visit for every exported field of the struct v, descending into nested structs other than Secret.
func walk(v reflect.Value, envPrefix, path string, visit func(field)) {
	t := v.Type()
	for i := range t.NumField() {
		sf := t.Field(i)
		if !sf.IsExported() {
			continue
		}
		f := field{
			path:      strings.TrimPrefix(path+"."+sf.Name, "."),
			yamlKey:   strings.Split(sf.Tag.Get("yaml"), ",")[0],
			envName:   strings.Split(sf.Tag.Get("env"), ",")[0],
			envPrefix: sf.Tag.Get("envPrefix"),
			secret:    sf.Type == secretType,
			value:     v.Field(i),
		}
		f.nested = sf.Type.Kind() == reflect.Struct && !f.secret
		if f.envName != "" {
			f.envKey = envPrefix + f.envName
		}
		visit(f)
		if f.nested {
			walk(v.Field(i), envPrefix+f.envPrefix, f.path, visit)
		}
	}
}

func processEnvironment() map[string]string {
	environment := map[string]string{}
	for _, entry := range os.Environ() {
		if key, value, ok := strings.Cut(entry, "="); ok {
			environment[key] = value
		}
	}
	return environment
}
