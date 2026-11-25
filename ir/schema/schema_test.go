package schema

import (
	"encoding/json"
	"io/fs"
	"testing"
)

func TestSchemaEmbedsEveryKindOfVersion0(t *testing.T) {
	for _, name := range []string{"common", "document", "node_type"} {
		data, err := fs.ReadFile(Schema, "v0/"+name+".schema.json")
		if err != nil {
			t.Fatalf("reading %s: %v", name, err)
		}
		if !json.Valid(data) {
			t.Errorf("%s is not valid JSON", name)
		}
	}
}
