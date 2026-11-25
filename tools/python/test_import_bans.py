"""The linter rejects any import of one workspace member by another, except of the members it depends on.

A member's dependencies on other members are those its pyproject.toml declares.
"""

import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Any

import pytest
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

ROOT = Path(__file__).parents[2]
MEMBERS: list[str] = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["uv"]["workspace"][
    "members"
]
FORMS = ["import {0}", "from {0}.module import name", "from {0} import name"]


def pyproject(member: str) -> dict[str, Any]:
    return tomllib.loads((ROOT / member / "pyproject.toml").read_text(encoding="utf-8"))


def module(member: str) -> str:
    # A member whose module sits in a shared namespace, such as ir.schema, names it apart from its distribution.
    config = pyproject(member)
    return config.get("tool", {}).get("uv", {}).get("build-backend", {}).get("module-name", config["project"]["name"])


def allowed(member: str) -> set[str]:
    names = {
        canonicalize_name(Requirement(requirement).name) for requirement in pyproject(member)["project"]["dependencies"]
    }
    return {other for other in MEMBERS if canonicalize_name(pyproject(other)["project"]["name"]) in names}


def banned(member: str) -> list[str]:
    return [other for other in MEMBERS if other != member and other not in allowed(member)]


def ban_messages(member: str, source: str) -> list[str]:
    # Linting stdin under a path inside the member applies the member's own configuration.
    probe = f"{member}/src/{module(member).replace('.', '/')}/probe.py"
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
    assert ban_messages(member, form.format(module(name)) + "\n")


@pytest.mark.parametrize(("member", "name"), [(member, name) for member in MEMBERS for name in allowed(member)])
def test_allows_dependency(member: str, name: str) -> None:
    assert ban_messages(member, f"import {module(name)}\n") == []
