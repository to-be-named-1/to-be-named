#!/bin/sh
# Checks the IR schema and its conformance corpus (make ir-check), in the ir-check container.
#
# For every IR version: each schema compiles, every document under valid/ passes and every document
# under invalid/schema/ fails. Documents under invalid/subset/ break the YAML subset, which a JSON Schema
# validator cannot see; the compiler's tests check them.
set -eu

JV_VERSION=v0.7.0
IR=controlplane/internal/authoring/ir

if ! go install "github.com/santhosh-tekuri/jsonschema/cmd/jv@${JV_VERSION}" >/tmp/jv-install.log 2>&1; then
	cat /tmp/jv-install.log
	exit 2
fi

failures=0
for schema_dir in "$IR"/schema/v*/; do
	version=$(basename "$schema_dir")
	document="$schema_dir/document.schema.json"
	corpus="$IR/conformance/$version"

	for schema in "$schema_dir"*.schema.json; do
		if ! jv -q "$schema" >/dev/null; then
			echo "error: $schema does not compile"
			failures=$((failures + 1))
		fi
	done

	for file in "$corpus"/valid/*.yaml; do
		[ -e "$file" ] || continue
		if ! jv -q "$document" "$file" >/dev/null; then
			echo "error: $file should be valid"
			jv "$document" "$file" || true
			failures=$((failures + 1))
		fi
	done

	for file in "$corpus"/invalid/schema/*.yaml; do
		[ -e "$file" ] || continue
		status=0
		jv -q "$document" "$file" >/dev/null || status=$?
		if [ "$status" -ne 1 ]; then
			echo "error: $file should fail validation (jv exit status $status)"
			failures=$((failures + 1))
		fi
	done
done

echo "ir-check: $failures error(s)"
[ "$failures" -eq 0 ]
