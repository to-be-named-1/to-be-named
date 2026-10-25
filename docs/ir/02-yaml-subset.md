# YAML subset

The text form of the IR is YAML restricted so that every document holds the same values in every tool that reads it ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md), [D56](../architecture/decisions/0056-ir-documents-and-identifiers.md)).

## Data model

Every document MUST decode to the data model of I-JSON ([RFC 7493](https://www.rfc-editor.org/rfc/rfc7493)): mappings whose keys are strings, lists, numbers, `true`, `false` and `null`. A document therefore converts to JSON without loss, and its schema validates that value.

## Syntax

A document:

- MUST be exactly one YAML document, encoded in UTF-8 without a byte-order mark.
- MAY use block and flow collections, comments, and plain, single-quoted, double-quoted, literal (`|`) and folded (`>`) scalars.
- MUST NOT use:

| Construct | Example | Reason |
|---|---|---|
| Anchors and aliases | `&base`, `*base` | They do not survive a structured write-back ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)), and aliases can expand a small file into a very large value |
| Merge keys | `<<: *base` | They depend on aliases |
| Tags | `!!str 5`, `!custom` | They give values types outside the data model ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)) |
| Directives | `%YAML 1.2` | The specification fixes the rules |
| Several documents | `---` between documents | One document per file ([D41](../architecture/decisions/0041-ir-text-form-round-trip-and-structure.md)) |
| Keys that are not strings | `1: x`, `? [a, b]: x` | Keys in the data model are strings |

A duplicated key in a mapping is an error. Writers write line feeds; readers MUST accept carriage return and line feed.

## Unquoted values

A reader MUST type a quoted, literal or folded scalar as a string. It MUST type an unquoted (plain) scalar by the following rules, never by the typing of a YAML library:

1. **Numbers.** A plain value that begins with a digit, `+`, `-` or `.` MUST be an integer, `-?(0|[1-9][0-9]*)`, or a number, `-?(0|[1-9][0-9]*)\.[0-9]+([eE][-+]?[0-9]+)?`. A reader MUST reject any other plain value that begins with one of those characters.
2. **Words.** A plain value that, ignoring case, is `true`, `false`, `null`, `y`, `n`, `yes`, `no`, `on` or `off`, or that is `~`, MUST be lowercase `true` or `false`, which are booleans, or lowercase `null`. A reader MUST reject any other such value.
3. **Empty.** An empty plain value is null, as in every YAML parser.
4. **Strings.** Every other plain value is a string.

Every unquoted value that YAML parsers type in different ways falls under rule 1 or rule 2: numbers in other bases, with separators or without a digit on each side of the point, dates and times, sexagesimal values, infinities and NaN all begin with a digit, a sign or a point, and the remaining cases are those words. For a rejected value, a reader SHOULD state the quoted form and the number or boolean that may have been meant. For example:

| Unquoted value | Rule | Write instead |
|---|---|---|
| `no`, `Yes`, `on`, `y` | 2 | `"no"`, or `false` for a boolean |
| `True`, `NULL`, `~` | 2 | `true`, `null`, or `"~"` for a string |
| `012`, `0x1F`, `1_000`, `+1`, `1:30` | 1 | `"012"`, or `12` for the number |
| `1e3` | 1 | `1.0e3` for the number, `"1e3"` for a string |
| `.5`, `5.`, `-.5` | 1 | `0.5`, `5.0`, or the quoted form for a string |
| `.inf`, `.nan` | 1 | Not representable |
| `2026-10-01`, `12:30` | 1 | `"2026-10-01"`; a field typed as a date validates its format |
| `-draft`, `.hidden` | 1 | `"-draft"`, `".hidden"` |

The same rules apply to unquoted keys. Keys the specification defines and identifiers never need quoting.

Writers MUST quote the empty string and every string that rules 1 and 2 would reject or read as another type.

## Numbers

- An integer MUST lie within ±(2^53−1), the range a browser represents exactly. A larger whole value, such as an external identifier, is written as a string.
- A number is an IEEE 754 double-precision value. Infinities and NaN are not representable.

## Enforcement

A reader MUST apply these rules to the YAML syntax tree, where quoting, tags, anchors and aliases are still visible, and build the document's value from it before validating the value against the schema.
