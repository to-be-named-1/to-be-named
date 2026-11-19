"""The linter rejects any import of one workspace member by another, except imports of sdk by the others."""

import json
import subprocess
import sys
import tomllib
from pathlib import Path

import pytest

ROOT = Path(__file__).parents[2]
WORKSPACE = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
MEMBERS: list[str] = WORKSPACE["tool"]["uv"]["workspace"]["members"]
SDK = "sdk"
FORMS = ["import {0}", "from {0}.module import name", "from {0} import name"]


def banned(member: str) -> list[str]:
    return [other for other in MEMBERS if other != member and (member == SDK or other != SDK)]


def ban_messages(member: str, source: str) -> list[str]:
    # Linting stdin under a path inside the member applies the member's own configuration.
    probe = f"{member}/src/{member}/probe.py"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--output-format", "json", "--stdin-filename", probe, "-"],
        input=source,
        capture_output=True,
        text=True,
        cwd=ROOT,
        check=False,
    )
    return [d["message"] for d in json.loads(result.stdout) if d["code"] == "TID251"]


@pytest.mark.parametrize(
    ("member", "name", "form"),
    [(member, name, form) for member in MEMBERS for name in banned(member) for form in FORMS],
)
def test_rejects_banned_import(member: str, name: str, form: str) -> None:
    assert ban_messages(member, form.format(name) + "\n")


@pytest.mark.parametrize("member", [member for member in MEMBERS if member != SDK])
def test_allows_sdk(member: str) -> None:
    assert ban_messages(member, "import sdk\n") == []
