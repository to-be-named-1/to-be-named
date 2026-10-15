#!/usr/bin/env python3
"""Turns bare references in the architecture documentation into Markdown links that Structurizr resolves.

Structurizr resolves a relative link only to a file of the same set: from one ADR to another, or
between files of one documentation set. A link that crosses sets uses Structurizr's `{workspace}`
prefix, which it rewrites to the workspace's own pages; such a link resolves in Structurizr, the
primary reader, and not on GitHub.

  D29         -> 0029-....md from an ADR; {workspace}/decisions/Platform#29 from documentation.
                 On an ADR's status-block lines (Amends, Amended by, Supersedes, Superseded by)
                 the link reads "29. Title".
  S25         -> the open item's numbered section: 07-open-items.md#3.1 from the workspace
                 documentation, {workspace}/documentation#3.1 from anywhere else; the file's
                 section alone while the item has no heading of its own.
  CORE 2.6    -> the capability line in 03-capabilities-core.md, likewise (DE, DS and MLE too).

Each container's documentation, model/platform/<container>/docs/, is a set of its own, at
{workspace}/documentation/<system>/<container name>, with the name percent-encoded.

Section numbers are the ones Structurizr assigns: a set's files in name order, each file's `##`
heading numbered by its position and its `###` headings numbered within it. They change as files
are added, so every link whose text is an ID is recomputed on each run, and a relative link to a
file of another set is rewritten to that file's section.

A reference is linked only when its target file exists, and never to the file it appears in.
Left alone: inline and fenced code, headings, lines about content pending migration (they refer to
the design record), and bare "S3", which is also the name of Amazon S3; a reference to open item S3
is linked by hand and then kept current like any other.

  python tools/docs/link.py            rewrite files in place
  python tools/docs/link.py --check    list references to link or correct; exit status 1 if any
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote, unquote

DECISION = re.compile(r"(?<![\w/.#\[-])D(\d{1,3})\b(?![\w-])")
OPEN_ITEM = re.compile(r"(?<![\w/.#\[-])S(\d{1,3})\b(?![\w-])")
CAPABILITY = re.compile(r"(?<![\w/.#\[-])(CORE|DE|DS|MLE) (\d+(?:\.\d+)?)\b(?![\w-])")
PROTECTED = re.compile(r"!?\[[^\]]*\]\([^)]*\)|`[^`]*`|<[^>]+>")
LINK = re.compile(r"(!?)\[([^\]]*)\]\(([^)\s]+)\)")
DECISION_TEXT = re.compile(r"^D(\d{1,3})$")
OPEN_ITEM_TEXT = re.compile(r"^S(\d{1,3})$")
CAPABILITY_TEXT = re.compile(r"^(CORE|DE|DS|MLE) (\d+(?:\.\d+)?)$")
CAPABILITY_FILES = {
    "CORE": "03-capabilities-core.md",
    "DE": "04-capabilities-de.md",
    "DS": "05-capabilities-ds.md",
    "MLE": "06-capabilities-mle.md",
}
UNLINKED_OPEN_ITEMS = {3}
STATUS_LINK_LINE = re.compile(r"^(Amends|Amended by|Supersedes|Superseded by) ")
ADR_TITLE = re.compile(r"^# (\d+\. .+)$")
SYSTEM_NAME = re.compile(r'^\s*platform\s*=\s*softwareSystem\s+"([^"]+)"', re.MULTILINE)
CONTAINER_NAME = re.compile(r'^\s*\w+\s*=\s*container\s+"([^"]+)"', re.MULTILINE)
WORKSPACE = "{workspace}"
SKIPPED = ("http://", "https://", "mailto:", "#", "embed:", WORKSPACE)


def adr_title(path: Path) -> str:
    """The 'N. Title' of an ADR, as written on its first line."""
    first = path.read_text(encoding="utf-8").split("\n", 1)[0]
    match = ADR_TITLE.match(first)
    return match[1] if match else f"{int(path.name[:4])}"


def headings3(path: Path) -> list[str]:
    """The text of a file's `###` headings, in order, outside fenced code."""
    found, fence = [], None
    for line in path.read_text(encoding="utf-8").split("\n"):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = marker if fence is None else (None if marker == fence else fence)
        elif fence is None and line.startswith("### "):
            found.append(line[4:].strip())
    return found


def relative(source: Path, target: Path) -> str:
    return os.path.relpath(target, start=source.parent).replace(os.sep, "/")


class Layout:
    """Where each reference points, and the section numbers Structurizr gives each documentation set."""

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self.decisions_dir = (root / "decisions").resolve()
        self.workspace_dir = (root / "documentation" / "workspace").resolve()
        self.platform_dir = (root / "documentation" / "platform").resolve()
        dsl = root / "workspace.dsl"
        match = SYSTEM_NAME.search(dsl.read_text(encoding="utf-8")) if dsl.is_file() else None
        self.system = match[1] if match else "Platform"
        self.adrs = {int(p.name[:4]): p.resolve() for p in self.decisions_dir.glob("*.md") if p.name[:4].isdigit()}
        open_items = self.workspace_dir / "07-open-items.md"
        self.open_items = open_items if open_items.is_file() else None
        self.capabilities = {
            family: self.workspace_dir / name
            for family, name in CAPABILITY_FILES.items()
            if (self.workspace_dir / name).is_file()
        }
        # Container documentation sets: docs/ folder -> container name, from the folder's container.dsl.
        self.container_docs: dict[Path, str] = {}
        for dsl in sorted((root / "model" / "platform").glob("*/container.dsl")):
            docs = dsl.parent / "docs"
            match = CONTAINER_NAME.search(dsl.read_text(encoding="utf-8"))
            if match and docs.is_dir():
                self.container_docs[docs.resolve()] = match[1]

    def documentation_url(self, directory: Path) -> str | None:
        directory = directory.resolve()
        if directory == self.workspace_dir:
            return f"{WORKSPACE}/documentation"
        if directory == self.platform_dir:
            return f"{WORKSPACE}/documentation/{self.system}"
        if directory in self.container_docs:
            return f"{WORKSPACE}/documentation/{self.system}/{quote(self.container_docs[directory])}"
        return None

    def documentation_dir(self, scope: str | None) -> Path | None:
        """The documentation set a `{workspace}/documentation[/scope]` link names, or None."""
        if scope is None:
            return self.workspace_dir
        if scope == self.system:
            return self.platform_dir
        system, _, container = scope.partition("/")
        if system == self.system and container:
            for directory, name in self.container_docs.items():
                if name == unquote(container):
                    return directory
        return None

    @staticmethod
    def section(path: Path) -> int:
        names = sorted(p.name for p in path.parent.glob("*.md"))
        return names.index(path.name) + 1

    def anchor(self, path: Path, item: str | None = None) -> str:
        """`n` for the file's section, or `n.m` for the `###` heading that begins with the item's ID."""
        number = self.section(path)
        if item:
            pattern = re.compile(rf"^{re.escape(item)}(?=[\s·:]|$)")
            for index, heading in enumerate(headings3(path), start=1):
                if pattern.match(heading):
                    return f"{number}.{index}"
        return f"{number}"

    def anchors(self, directory: Path) -> set[str]:
        """Every section and subsection number of one documentation set."""
        found = set()
        for path in sorted(directory.glob("*.md")):
            number = self.section(path)
            found.add(f"{number}")
            found.update(f"{number}.{index}" for index in range(1, len(headings3(path)) + 1))
        return found

    def href(self, source: Path, target: Path, item: str | None = None) -> str | None:
        """The link from `source` to `target` (an ADR or a documentation file), at `item` where given."""
        target = target.resolve()
        same_set = target.parent == source.resolve().parent
        if target.parent == self.decisions_dir:
            if same_set:
                return target.name
            return f"{WORKSPACE}/decisions/{self.system}#{int(target.name[:4])}"
        if same_set:
            anchor = self.anchor(target, item) if item else None
            return target.name + (f"#{anchor}" if anchor and "." in anchor else "")
        url = self.documentation_url(target.parent)
        if url is None:
            return relative(source, target)
        return f"{url}#{self.anchor(target, item)}"

    def resolve_reference(self, text: str, current: str | None = None) -> tuple[Path, str | None] | None:
        """The target file and item of a link whose text is an ID, or None if the text is not one."""
        if match := DECISION_TEXT.match(text):
            target = self.adrs.get(int(match[1]))
            return (target, None) if target else None
        if match := OPEN_ITEM_TEXT.match(text):
            number = int(match[1])
            points_to_open_items = current is not None and (
                current.split("#", 1)[0].endswith("07-open-items.md")
                or current.startswith(f"{WORKSPACE}/documentation#")
            )
            if self.open_items and (number not in UNLINKED_OPEN_ITEMS or points_to_open_items):
                return self.open_items, f"S{number}"
            return None
        if match := CAPABILITY_TEXT.match(text):
            target = self.capabilities.get(match[1])
            return (target, f"{match[1]} {match[2]}") if target else None
        return None


def process(path: Path, layout: Layout, check: bool) -> list[str]:
    findings: list[str] = []
    lines = path.read_text(encoding="utf-8").split("\n")
    in_decisions = path.resolve().parent == layout.decisions_dir
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = marker if fence is None else (None if marker == fence else fence)
            continue
        if fence is not None or stripped.startswith("#") or "pending migration" in line:
            continue
        where = f"{path.as_posix()}:{index + 1}"
        status_line = in_decisions and STATUS_LINK_LINE.match(line)

        # Existing links: keep the text of status-block links current, and point every link whose
        # text is an ID, or that crosses into another set, where Structurizr resolves it.
        def correct(match: re.Match) -> str:
            image, text, current = match[1], match[2], match[3]
            if image:
                return match[0]
            if status_line and re.fullmatch(r"\d{4}-[a-z0-9-]+\.md", current):
                target = path.parent / current
                if not target.is_file():
                    return match[0]
                title = adr_title(target)
                if text != title:
                    findings.append(f"{where}: link text {text!r} should read {title!r}")
                return f"[{title}]({current})"
            desired = None
            reference = layout.resolve_reference(text, current)
            if reference and reference[0].resolve() != path.resolve():
                desired = layout.href(path, reference[0], reference[1])
            elif not current.startswith(SKIPPED):
                file_part = current.split("#", 1)[0].split("?", 1)[0]
                resolved = (path.parent / file_part).resolve() if file_part else None
                if (resolved and resolved.suffix == ".md" and resolved.is_file()
                        and layout.root in resolved.parents and resolved.parent != path.resolve().parent):
                    desired = layout.href(path, resolved)
            if desired and desired != current:
                findings.append(f"{where}: link {text!r} should point to {desired}")
                return f"[{text}]({desired})"
            return match[0]

        line = LINK.sub(correct, line)
        protected = [m.span() for m in PROTECTED.finditer(line)]

        def free(span):
            return not any(start < span[1] and span[0] < end for start, end in protected)

        replacements = []
        for match in DECISION.finditer(line):
            target = layout.adrs.get(int(match[1]))
            if target and target != path.resolve() and free(match.span()):
                text = adr_title(target) if status_line else f"D{int(match[1])}"
                replacements.append((match.span(), f"[{text}]({layout.href(path, target)})"))
        for match in OPEN_ITEM.finditer(line):
            number = int(match[1])
            if (layout.open_items and number not in UNLINKED_OPEN_ITEMS
                    and layout.open_items.resolve() != path.resolve() and free(match.span())):
                replacements.append((match.span(), f"[S{number}]({layout.href(path, layout.open_items, f'S{number}')})"))
        for match in CAPABILITY.finditer(line):
            target = layout.capabilities.get(match[1])
            if target and target.resolve() != path.resolve() and free(match.span()):
                item = f"{match[1]} {match[2]}"
                replacements.append((match.span(), f"[{item}]({layout.href(path, target, item)})"))

        for (start, end), link in sorted(replacements, reverse=True):
            findings.append(f"{where}: bare reference {line[start:end]}")
            line = line[:start] + link + line[end:]
        lines[index] = line

    if findings and not check:
        path.write_bytes("\n".join(lines).encode("utf-8"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path("docs/architecture"))
    parser.add_argument("--check", action="store_true", help="report references without rewriting")
    args = parser.parse_args()
    layout = Layout(args.root)
    findings = []
    for path in sorted(args.root.rglob("*.md")):
        findings += process(path, layout, args.check)
    if args.check:
        for finding in findings:
            print(f"error: {finding}")
        print(f"docs-link: {len(findings)} reference(s) to link or correct")
        return 1 if findings else 0
    print(f"docs-link: {len(findings)} reference(s) linked or corrected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
