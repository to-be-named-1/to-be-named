"""The IR schema: one JSON Schema 2020-12 document per kind, for each IR version (docs/ir)."""

import json
from importlib.resources import files
from typing import Any


def schema(name: str, version: int) -> dict[str, Any]:
    """Return a schema document of an IR version, with its properties in the order the file lists them.

    Args:
        name: The schema's name, such as "node_type", "document" or "common".
        version: The IR version.
    """
    path = files(__name__).joinpath(f"v{version}", f"{name}.schema.json")
    return json.loads(path.read_text(encoding="utf-8"))
