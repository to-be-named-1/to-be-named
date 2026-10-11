#!/usr/bin/env python3
"""Turns bare references in the architecture documentation into relative Markdown links.

  D29         -> the ADR file decisions/0029-....md; on an ADR's status-block lines
                 (Amends, Amended by, Supersedes, Superseded by) the link reads "29. Title"
  S25         -> documentation/workspace/07-open-items.md
  CORE 2.6    -> documentation/workspace/03-capabilities-core.md (DE, DS and MLE likewise)

A reference is linked only when its target file exists, and never to the file it appears in.
Left alone: existing links, inline and fenced code, headings, lines about content pending
migration (they refer to the design record), and "S3", which is also the name of Amazon S3;
a reference to open item S3 is linked by hand.

  python tools/docs/link.py            rewrite files in place
  python tools/docs/link.py --check    list bare references; exit status 1 if any remain
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

DECISION = re.compile(r"(?<![\w/.#\[-])D(\d{1,3})\b(?![\w-])")
OPEN_ITEM = re.compile(r"(?<![\w/.#\[-])S(\d{1,3})\b(?![\w-])")
CAPABILITY = re.compile(r"(?<![\w/.#\[-])(CORE|DE|DS|MLE) (\d+(?:\.\d+)?)\b(?![\w-])")
PROTECTED = re.compile(r"!?\[[^\]]*\]\([^)]*\)|`[^`]*`|<[^>]+>")
CAPABILITY_FILES = {
    "CORE": "03-capabilities-core.md",
    "DE": "04-capabilities-de.md",
    "DS": "05-capabilities-ds.md",
    "MLE": "06-capabilities-mle.md",
}
UNLINKED_OPEN_ITEMS = {3}
STATUS_LINK_LINE = re.compile(r"^(Amends|Amended by|Supersedes|Superseded by) ")
ADR_TITLE = re.compile(r"^# (\d+\. .+)$")


def adr_title(path: Path) -> str:
    """The 'N. Title' of an ADR, as written on its first line."""
    first = path.read_text(encoding="utf-8").split("\n", 1)[0]
    match = ADR_TITLE.match(first)
    return match[1] if match else f"{int(path.name[:4])}"


def targets(root: Path):
    decisions = {}
    for path in (root / "decisions").glob("*.md"):
        if path.name[:4].isdigit():
            decisions[int(path.name[:4])] = path
    workspace = root / "documentation" / "workspace"
    open_items = workspace / "07-open-items.md"
    capabilities = {family: workspace / name for family, name in CAPABILITY_FILES.items()}
    return decisions, (open_items if open_items.is_file() else None), {
        family: path for family, path in capabilities.items() if path.is_file()
    }


def relative(source: Path, target: Path) -> str:
    return os.path.relpath(target, start=source.parent).replace(os.sep, "/")


def process(path: Path, root: Path, check: bool) -> list[str]:
    decisions, open_items, capabilities = targets(root)
    findings: list[str] = []
    lines = path.read_text(encoding="utf-8").split("\n")
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith(("```", "~~~")):
            marker = stripped[:3]
            fence = marker if fence is None else (None if marker == fence else fence)
            continue
        if fence is not None or stripped.startswith("#") or "pending migration" in line:
            continue
        protected = [m.span() for m in PROTECTED.finditer(line)]

        def free(span):
            return not any(start < span[1] and span[0] < end for start, end in protected)

        # On an ADR's status-block lines the link reads "N. Title"; in prose it reads "Dn".
        status_line = path.parent.resolve() == (root / "decisions").resolve() and STATUS_LINK_LINE.match(line)
        if status_line:
            def retitle(match: re.Match) -> str:
                target = path.parent / match[2]
                if not target.is_file():
                    return match[0]
                title = adr_title(target)
                if match[1] != title:
                    findings.append(f"{path.as_posix()}:{index + 1}: link text {match[1]!r} should read {title!r}")
                return f"[{title}]({match[2]})"
            line = re.sub(r"\[([^\]]*)\]\((\d{4}-[a-z0-9-]+\.md)\)", retitle, line)
            protected = [m.span() for m in PROTECTED.finditer(line)]
        replacements = []
        for match in DECISION.finditer(line):
            target = decisions.get(int(match[1]))
            if target and target.resolve() != path.resolve() and free(match.span()):
                text = adr_title(target) if status_line else f"D{int(match[1])}"
                replacements.append((match.span(), f"[{text}]({relative(path, target)})"))
        for match in OPEN_ITEM.finditer(line):
            number = int(match[1])
            if (open_items and number not in UNLINKED_OPEN_ITEMS
                    and open_items.resolve() != path.resolve() and free(match.span())):
                replacements.append((match.span(), f"[S{number}]({relative(path, open_items)})"))
        for match in CAPABILITY.finditer(line):
            target = capabilities.get(match[1])
            if target and target.resolve() != path.resolve() and free(match.span()):
                replacements.append((match.span(), f"[{match[1]} {match[2]}]({relative(path, target)})"))

        for (start, end), link in sorted(replacements, reverse=True):
            findings.append(f"{path.as_posix()}:{index + 1}: bare reference {line[start:end]}")
            line = line[:start] + link + line[end:]
        lines[index] = line

    if findings and not check:
        path.write_bytes("\n".join(lines).encode("utf-8"))
    return findings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path("docs/architecture"))
    parser.add_argument("--check", action="store_true", help="report bare references without rewriting")
    args = parser.parse_args()
    findings = []
    for path in sorted(args.root.rglob("*.md")):
        findings += process(path, args.root, args.check)
    if args.check:
        for finding in findings:
            print(f"error: {finding}")
        print(f"docs-link: {len(findings)} reference(s) to link or correct")
        return 1 if findings else 0
    print(f"docs-link: {len(findings)} reference(s) linked or corrected")
    return 0


if __name__ == "__main__":
    sys.exit(main())
