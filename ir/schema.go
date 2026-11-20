// Package ir holds the IR schema, one JSON Schema 2020-12 document per kind for each IR version (docs/ir). The
// same files are published as a Python package of the same name.
package ir

import (
	"embed"
	"io/fs"
)

// The files live inside the Python package, so that both languages publish the same copy.
//
//go:embed src/ir/schema
var files embed.FS

// Schema holds the schema files, at v<version>/<kind>.schema.json.
var Schema = sub(files, "src/ir/schema")

func sub(fsys fs.FS, dir string) fs.FS {
	tree, err := fs.Sub(fsys, dir)
	if err != nil {
		panic(err)
	}
	return tree
}
