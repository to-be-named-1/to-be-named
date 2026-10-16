#!/usr/bin/env python3
"""Checks for the architecture documentation in docs/architecture.

Run by `make docs-check`, after `structurizr validate` and a JSON export of the workspace.

  1. ADR files: file name, title number, Date, status, labeled links and their symmetry,
     section order; dates never decrease as numbers rise, since Structurizr orders the
     decision log by date and then by number.
  2. `decisions` properties on elements and relationships name existing ADRs, and every
     migrated ADR's "Applies to" line agrees with the elements that cite it.
  3. No forbidden relationship (tools/docs/forbidden-edges.json), explicit or implied; a rule
     marked across_groups forbids only explicit relationships that reach a grouped element from
     outside its group.
  4. Every overlay file carries its header.
  5. Markdown: documentation files begin with one `##` heading, the README with one `#`;
     relative links resolve and stay within one set (an ADR to an ADR, or within one
     documentation set); links across sets use Structurizr's `{workspace}` form and name an
     existing ADR or section; links to ADRs read `Dn` or `N. Title` with the right number.
     (Bare references and outdated section numbers are reported by tools/docs/link.py --check.)
  6. No British spelling is used anywhere under docs/.
  7. Roles and container documentation: a component is tagged `Leader only` exactly when its only
     role is `leader`; a row of a container's 03-components.md that names one of its
     components gives the model's description in its second column, and an "Actions by role"
     column labels exactly the component's roles; every component has a row; 09-decisions.md
     lists exactly the container's decisions property.
  8. Deployment routing: in an environment with more than one control-plane instance, no web
     application, CLI or agent instance connects to a control-plane instance directly; traffic
     reaches the roles through a routing node, so a missing or misspelled deployment group fails.
  9. With --cutover: the count check required before project-design.md is retired, including
     that each reasoning item of the record sits in exactly one ADR's Context, and that no
     permanent file refers to the record.

Standard library only. Exit status 1 if any error is reported.
"""

from __future__ import annotations

import argparse
import datetime
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import link as linker  # noqa: E402

STATUSES = {"Accepted", "Partial", "Superseded", "Rejected"}
SECTIONS = [
    "Status",
    "Context",
    "Decision",
    "Consequences",
    "Rejected alternatives",
    "Follow-ups",
]
INVERSE_LINK = {
    "Amends": "Amended by",
    "Amended by": "Amends",
    "Supersedes": "Superseded by",
    "Superseded by": "Supersedes",
}
PENDING = "Content pending migration"
OVERLAY_FIELDS = ("// Overlay:", "// Purpose:", "// Remove when:")

ADR_NAME = re.compile(r"^(\d{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
ADR_TITLE = re.compile(r"^# (\d+)\. (\S.*)$")
ADR_LINK = re.compile(
    r"^(Amends|Amended by|Supersedes|Superseded by) \[([^\]]+)\]\((\d{4}-[a-z0-9-]+\.md)\)$"
)
DECISION_REF = re.compile(r"\bD(\d+)\b")
MD_LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
INLINE_CODE = re.compile(r"`[^`]*`")
SKIPPED_LINK_PREFIXES = ("http://", "https://", "mailto:", "#", "embed:")
WORKSPACE_DECISION_LINK = re.compile(r"^\{workspace\}/decisions/([^#]+)#(\d+)$")
WORKSPACE_DOCUMENTATION_LINK = re.compile(r"^\{workspace\}/documentation(?:/([^#]+))?#(\d+(?:\.\d+)?)$")

CUTOVER_DECISIONS = 50
CUTOVER_PARTIAL = {27}
CUTOVER_OPEN_ITEMS = 25
CUTOVER_CAPABILITIES = {"CORE": 103, "DE": 36, "DS": 31, "MLE": 25}
CUTOVER_REASONING_ITEMS = 69
# Reasoning items whose title changes when it is carried over: a mention of comparable software
# is dropped, or the spelling becomes American.
CUTOVER_TITLE_CHANGES = {
    3: "Containers rather than a single process",
    10: "Tenant = the whole organization",
    54: "A leader-centered control plane with invariants in the database",
}
# Reasoning items removed from their ADR after migration; the cut-over check does not look for them.
CUTOVER_DROPPED_REASONING_ITEMS = {
    62,  # "Spark is not a general remedy for resource exhaustion" (D47)
}
# British spellings the documentation must not use; American English is the register.
_BRITISH_IZE_ROOTS = (
    "author|material|normal|optim|special|synchron|serial|initial|priorit|recogn|summar|visual|minim|maxim|"
    "standard|custom|categor|util|parallel|container|canonical|memo|token|random|character|final|organ|real|"
    "capital|central|general|local|global|emphas|apolog|harmon|stabil|neutral|legal|modern|privat|virtual|vector"
)
BRITISH_SPELLING = re.compile(
    r"\b(?:\w*(?:" + _BRITISH_IZE_ROOTS + r")is(?:e|ed|es|ing|er|ers|ation|ations|able)"
    r"|\w*(?:behavio|colo|favo|hono|labo|neighbo|flavo|harbo|rumo|humo|vapo|endeavo)ur(?:s|ed|ing|able|ite|ites|al|ally)?"
    r"|catalogu(?:e|es|ed|ing)|licences?|defence|offence|pretence"
    r"|analys(?:e|ed|ing|able)|paralys(?:e|ed)|catalys(?:e|ed)|centres?|centred|metres?|fibre|theatre"
    r"|artefacts?|labell(?:ed|ing)|modell(?:ed|ing|er|ers)|cancell(?:ed|ing)|travell(?:ed|ing|er)|signall(?:ed|ing)"
    r"|enrols|enrolment|fulfils?|fulfilment|programmes?|grey|ageing|whilst|amongst|learnt|spelt|practis(?:e|ed|ing))\b",
    re.I,
)
RECORD_REFERENCE = re.compile(r"project-design|\bv0\.\d|\bPart I{1,3}\b|\bReasoning items? \d")


class Report:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.notes: list[str] = []

    def error(self, where: str, message: str) -> None:
        self.errors.append(f"{where}: {message}")

    def note(self, message: str) -> None:
        self.notes.append(message)


def display(path: Path) -> str:
    try:
        return path.resolve().relative_to(Path.cwd().resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def unfenced(lines: list[str]):
    """Yield (index, line) for lines outside fenced code blocks."""
    fence = None
    for index, line in enumerate(lines):
        stripped = line.lstrip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            marker = stripped[:3]
            if fence is None:
                fence = marker
            elif marker == fence:
                fence = None
            continue
        if fence is None:
            yield index, line


def decision_numbers(value: str | None) -> list[int]:
    return [int(n) for n in DECISION_REF.findall(value or "")]


# --- 1. ADRs -----------------------------------------------------------------------------


@dataclass
class Adr:
    number: int
    path: Path
    title: str
    date: datetime.date | None = None
    status: str | None = None
    applies_to: list[str] | None = None
    links: list[tuple[str, str, int]] = field(default_factory=list)
    link_texts: dict[str, str] = field(default_factory=dict)  # target file -> link text
    sections: list[str] = field(default_factory=list)
    pending: bool = False
    text: str = ""


def parse_adr(path: Path, report: Report) -> Adr | None:
    where = display(path)
    name = ADR_NAME.match(path.name)
    if not name:
        report.error(where, "file name must be NNNN-kebab-case-title.md")
        return None
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    title = ADR_TITLE.match(lines[0]) if lines else None
    if not title:
        report.error(f"{where}:1", "first line must be '# N. Title'")
        return None
    number = int(name[1])
    if int(title[1]) != number:
        report.error(f"{where}:1", f"title number {title[1]} does not match file number {number}")
    adr = Adr(number=number, path=path, title=title[2], text=text, pending=PENDING in text)

    headings = [(i, line[3:].strip()) for i, line in unfenced(lines) if line.startswith("## ")]
    adr.sections = [h for _, h in headings]
    for i, heading in headings:
        if heading not in SECTIONS:
            report.error(f"{where}:{i + 1}", f"unknown section '{heading}'")
    known = [h for h in adr.sections if h in SECTIONS]
    if len(known) != len(set(known)):
        report.error(where, "a section appears more than once")
    elif known != sorted(known, key=SECTIONS.index):
        report.error(where, "sections are out of order; expected " + ", ".join(SECTIONS))
    if not headings or headings[0][1] != "Status":
        report.error(where, "the first section must be '## Status'")
        return adr

    status_line = headings[0][0]
    date_seen = False
    for i in range(1, status_line):
        line = lines[i].strip()
        if not line:
            continue
        if line.startswith("Date: "):
            date_seen = True
            try:
                adr.date = datetime.date.fromisoformat(line[len("Date: "):].strip())
            except ValueError:
                report.error(f"{where}:{i + 1}", "Date must be YYYY-MM-DD")
        elif line.startswith("Applies to: "):
            adr.applies_to = [
                part.strip().strip("`") for part in line[len("Applies to: "):].split(",") if part.strip()
            ]
        else:
            report.error(f"{where}:{i + 1}", "only 'Date:' and 'Applies to:' lines may precede '## Status'")
    if not date_seen:
        report.error(where, "missing 'Date: YYYY-MM-DD' line (the importer would use the current date)")

    end = headings[1][0] if len(headings) > 1 else len(lines)
    block = [(i, lines[i].strip()) for i in range(status_line + 1, end) if lines[i].strip()]
    if not block:
        report.error(where, "the Status section is empty")
        return adr
    first_index, adr.status = block[0]
    if adr.status not in STATUSES:
        report.error(
            f"{where}:{first_index + 1}",
            f"status must be one word from {sorted(STATUSES)} (the importer reads only the first word)",
        )
    for i, line in block[1:]:
        link = ADR_LINK.match(line)
        if not link:
            report.error(f"{where}:{i + 1}", "lines after the status must be labeled links such as 'Amends [8. Title](0008-title.md)'")
            continue
        adr.links.append((link[1], link[3], i + 1))
        adr.link_texts[link[3]] = link[2]

    if not adr.pending:
        for required in ("Decision",):
            if required not in adr.sections:
                report.error(where, f"a migrated ADR needs a '## {required}' section")
        if adr.applies_to is None:
            report.error(where, "a migrated ADR needs an 'Applies to:' line")
    return adr


def check_adrs(decisions_dir: Path, report: Report) -> dict[int, Adr]:
    adrs: dict[int, Adr] = {}
    if not decisions_dir.is_dir():
        report.note("no decisions/ folder yet; ADR checks skipped")
        return adrs
    by_file: dict[str, Adr] = {}
    for path in sorted(decisions_dir.glob("*.md")):
        adr = parse_adr(path, report)
        if adr is None:
            continue
        if adr.number in adrs:
            report.error(display(path), f"number {adr.number} is already used by {adrs[adr.number].path.name}")
            continue
        adrs[adr.number] = adr
        by_file[path.name] = adr

    for adr in adrs.values():
        where = display(adr.path)
        for label, target, line in adr.links:
            other = by_file.get(target)
            if other is None:
                report.error(f"{where}:{line}", f"link target {target} does not exist")
                continue
            expected = f"{other.number}. {other.title}"
            if adr.link_texts.get(target) != expected:
                report.error(f"{where}:{line}", f"the link to {target} must read '{expected}'")
            inverse = INVERSE_LINK[label]
            if not any(l == inverse and t == adr.path.name for l, t, _ in other.links):
                report.error(f"{where}:{line}", f"{target} lacks the matching '{inverse}' link back to {adr.path.name}")
        superseded_by = any(label == "Superseded by" for label, _, _ in adr.links)
        if adr.status == "Superseded" and not superseded_by:
            report.error(where, "status Superseded needs a 'Superseded by' link")
        if superseded_by and adr.status != "Superseded":
            report.error(where, "a 'Superseded by' link needs status Superseded")
    dated = [adr for _, adr in sorted(adrs.items()) if adr.date is not None]
    for earlier, later in zip(dated, dated[1:]):
        if later.date < earlier.date:
            report.error(
                display(later.path),
                f"dated {later.date}, before ADR {earlier.number} ({earlier.date}); Structurizr orders the "
                "decision log by date, so a later number needs the same or a later date",
            )
    report.note(f"{len(adrs)} ADRs, {sum(a.pending for a in adrs.values())} pending migration")
    return adrs


# --- Workspace JSON ----------------------------------------------------------------------


@dataclass
class Model:
    elements: dict[str, dict] = field(default_factory=dict)  # id -> element
    parent: dict[str, str] = field(default_factory=dict)  # id -> parent id
    alias: dict[str, str] = field(default_factory=dict)  # instance id -> element id
    identifiers: dict[str, str] = field(default_factory=dict)  # DSL identifier -> id
    relationships: list[dict] = field(default_factory=list)


def load_model(path: Path) -> Model:
    workspace = json.loads(path.read_text(encoding="utf-8"))
    model = Model()

    def add(element: dict, parent_id: str | None) -> None:
        element_id = element["id"]
        model.elements[element_id] = element
        if parent_id is not None:
            model.parent[element_id] = parent_id
        identifier = (element.get("properties") or {}).get("structurizr.dsl.identifier")
        if identifier:
            model.identifiers[identifier] = element_id
        model.relationships.extend(element.get("relationships") or [])
        if "containerId" in element:
            model.alias[element_id] = element["containerId"]
        if "softwareSystemId" in element:
            model.alias[element_id] = element["softwareSystemId"]

    def add_deployment_node(node: dict, parent_id: str | None) -> None:
        add(node, parent_id)
        for child in node.get("children") or []:
            add_deployment_node(child, node["id"])
        for key in ("infrastructureNodes", "softwareSystemInstances", "containerInstances"):
            for item in node.get(key) or []:
                add(item, node["id"])

    data = workspace.get("model") or {}
    for key in ("people", "customElements"):
        for element in data.get(key) or []:
            add(element, None)
    for system in data.get("softwareSystems") or []:
        add(system, None)
        for container in system.get("containers") or []:
            add(container, system["id"])
            for component in container.get("components") or []:
                add(component, container["id"])
    for node in data.get("deploymentNodes") or []:
        add_deployment_node(node, None)
    return model


def ancestry(model: Model, element_id: str) -> list[str]:
    chain = []
    current: str | None = model.alias.get(element_id, element_id)
    while current is not None:
        chain.append(current)
        current = model.parent.get(current)
    return chain


# --- 2. Decisions and "Applies to" ---------------------------------------------------------


def check_traceability(model: Model, adrs: dict[int, Adr], have_adrs: bool, report: Report) -> None:
    cited: dict[int, set[str]] = {}
    for element_id, element in model.elements.items():
        properties = element.get("properties") or {}
        numbers = decision_numbers(properties.get("decisions"))
        if not numbers:
            continue
        identifier = properties.get("structurizr.dsl.identifier")
        name = identifier or element.get("name", element_id)
        if not identifier:
            report.error(f"element '{name}'", "an element with a decisions property needs a DSL identifier")
        for number in numbers:
            if have_adrs and number not in adrs:
                report.error(f"element '{name}'", f"decisions names D{number}, which has no ADR")
            if identifier:
                cited.setdefault(number, set()).add(identifier)
    for relationship in model.relationships:
        numbers = decision_numbers((relationship.get("properties") or {}).get("decisions"))
        for number in numbers:
            if have_adrs and number not in adrs:
                label = relationship.get("description") or relationship.get("id")
                report.error(f"relationship '{label}'", f"decisions names D{number}, which has no ADR")

    for number, adr in adrs.items():
        if adr.pending or adr.applies_to is None:
            continue
        where = display(adr.path)
        for identifier in adr.applies_to:
            if identifier not in model.identifiers:
                report.error(where, f"'Applies to' names {identifier}, which is not in the model")
            elif identifier not in cited.get(number, set()):
                report.error(where, f"{identifier} does not list D{number} in its decisions property")
        for identifier in sorted(cited.get(number, set()) - set(adr.applies_to)):
            report.error(where, f"{identifier} lists D{number}, but 'Applies to' does not name it")


# --- 3. Forbidden relationships ------------------------------------------------------------


def crosses_groups(model: Model, relationship: dict) -> bool:
    """True when an explicit relationship reaches a grouped element from outside that element's group."""
    if relationship.get("linkedRelationshipId"):
        return False
    source = model.elements.get(relationship["sourceId"], {})
    destination = model.elements.get(relationship["destinationId"], {})
    return bool(destination.get("group")) and source.get("group") != destination.get("group")


def check_forbidden_edges(model: Model, rules_path: Path, adrs: dict[int, Adr], have_adrs: bool,
                          cutover: bool, report: Report) -> None:
    rules = json.loads(rules_path.read_text(encoding="utf-8"))["rules"]
    inactive = 0
    for rule in rules:
        where = f"{display(rules_path)} [{rule['id']}]"
        for reference in rule.get("decisions", []):
            for number in decision_numbers(reference):
                if have_adrs and number not in adrs:
                    report.error(where, f"cites D{number}, which has no ADR")
        sources = {model.identifiers[i] for i in rule["from"] if i in model.identifiers}
        targets = {model.identifiers[i] for i in rule["to"] if i in model.identifiers}
        missing = [i for i in rule["from"] + rule["to"] if i not in model.identifiers]
        if missing:
            inactive += 1
            if cutover:
                report.error(where, "elements not in the model: " + ", ".join(missing))
        if not sources or not targets:
            continue
        for relationship in model.relationships:
            source_chain = ancestry(model, relationship["sourceId"])
            destination_chain = ancestry(model, relationship["destinationId"])
            if sources.intersection(source_chain) and targets.intersection(destination_chain):
                if rule.get("across_groups") and not crosses_groups(model, relationship):
                    continue
                source = model.elements.get(model.alias.get(relationship["sourceId"], relationship["sourceId"]), {})
                destination = model.elements.get(
                    model.alias.get(relationship["destinationId"], relationship["destinationId"]), {})
                implied = " (implied)" if relationship.get("linkedRelationshipId") else ""
                report.error(
                    where,
                    f"forbidden relationship{implied} {source.get('name')} -> {destination.get('name')} "
                    f"'{relationship.get('description', '')}': {rule['reason']} ({', '.join(rule['decisions'])})",
                )
    report.note(f"{len(rules)} forbidden-edge rules, {inactive} not yet fully in the model")


# --- 4. Overlays ---------------------------------------------------------------------------


def check_overlays(root: Path, report: Report) -> None:
    for folder in (root / "model" / "overlays", root / "views" / "overlays"):
        for path in sorted(folder.glob("*.dsl")) if folder.is_dir() else []:
            head = path.read_text(encoding="utf-8").splitlines()[:10]
            for prefix in OVERLAY_FIELDS:
                if not any(line.startswith(prefix) for line in head):
                    report.error(display(path), f"overlay header lacks a '{prefix}' line")


# --- 5. Markdown ---------------------------------------------------------------------------


def check_markdown(paths: list[Path], root: Path, report: Report) -> None:
    """Headings by kind of file, relative links, and the text of links to ADRs.

    Documentation files start with one `##` heading (Structurizr hides `#` and numbers `##`
    as sections); ADR headings are checked by parse_adr; the README outside the workspace
    starts with one `#` heading, as GitHub renders it.
    """
    decisions_dir = (root / "decisions").resolve()
    layout = linker.Layout(root)
    for path in paths:
        where = display(path)
        lines = path.read_text(encoding="utf-8").splitlines()
        content = list(unfenced(lines))
        first = next((i for i, line in enumerate(lines) if line.strip()), None)
        is_adr = path.resolve().parent == decisions_dir
        inside = root.resolve() in path.resolve().parents
        if not is_adr:
            h1 = [i for i, line in content if line.startswith("# ")]
            if inside:
                if h1:
                    report.error(f"{where}:{h1[0] + 1}", "documentation files use no '#' heading; Structurizr hides it")
                if first is None or not lines[first].startswith("## "):
                    report.error(where, "a documentation file must begin with its '##' section heading")
            elif len(h1) != 1 or h1[0] != first:
                report.error(where, "must begin with exactly one level-1 heading")
        for i, line in content:
            for match in MD_LINK.finditer(INLINE_CODE.sub("", line)):
                target = match[1]
                text = re.match(r"!?\[([^\]]*)\]", match[0])[1]
                if target.startswith("{workspace}"):
                    check_workspace_link(target, text, f"{where}:{i + 1}", layout, report)
                    continue
                if target.startswith(SKIPPED_LINK_PREFIXES):
                    continue
                relative = target.split("#", 1)[0].split("?", 1)[0]
                if not relative:
                    continue
                resolved = (path.parent / relative).resolve()
                if not resolved.exists():
                    report.error(f"{where}:{i + 1}", f"link target {target} does not exist")
                    continue
                if (inside and resolved.suffix == ".md" and root.resolve() in resolved.parents
                        and resolved.parent != path.resolve().parent):
                    report.error(f"{where}:{i + 1}", f"{target} crosses into another set, which Structurizr does not "
                                 "resolve; use the {workspace} form (make docs-link)")
                    continue
                if "#" in target and resolved.parent == path.resolve().parent and resolved.parent != decisions_dir:
                    anchor = target.split("#", 1)[1]
                    if anchor not in layout.anchors(resolved.parent) or not (
                            anchor == f"{layout.section(resolved)}" or anchor.startswith(f"{layout.section(resolved)}.")):
                        report.error(f"{where}:{i + 1}", f"{target} names no section of {resolved.name}")
                if resolved.parent == decisions_dir and resolved.name[:4].isdigit():
                    number = int(resolved.name[:4])
                    if text != f"D{number}" and not text.startswith(f"{number}. "):
                        report.error(f"{where}:{i + 1}", f"a link to ADR {number} must read 'D{number}' or '{number}. Title', not '{text}'")


def check_workspace_link(target: str, text: str, where: str, layout: "linker.Layout", report: Report) -> None:
    """A `{workspace}` link names an existing ADR, or an existing section of a documentation set."""
    if match := WORKSPACE_DECISION_LINK.match(target):
        number = int(match[2])
        if match[1] != layout.system:
            report.error(where, f"{target}: decisions live under '{layout.system}'")
        elif number not in layout.adrs:
            report.error(where, f"{target}: there is no ADR {number}")
        elif text != f"D{number}" and not text.startswith(f"{number}. "):
            report.error(where, f"a link to ADR {number} must read 'D{number}' or '{number}. Title', not '{text}'")
        return
    if match := WORKSPACE_DOCUMENTATION_LINK.match(target):
        directory = layout.documentation_dir(match[1])
        if directory is None:
            report.error(where, f"{target}: no documentation set is attached under '{match[1]}'")
        elif match[2] not in layout.anchors(directory):
            report.error(where, f"{target}: no section {match[2]} in {directory.name} documentation")
        return
    report.error(where, f"{target}: a {{workspace}} link must be {{workspace}}/decisions/{layout.system}#N or "
                 f"{{workspace}}/documentation[/{layout.system}[/<container name>]]#n[.m]")


# --- 6. American spelling -----------------------------------------------------------------


def check_spelling(docs: Path, report: Report) -> None:
    build = (docs / "build").resolve()
    for path in sorted(docs.rglob("*")):
        if path.suffix not in (".md", ".dsl") or build in path.resolve().parents:
            continue
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines()):
            for match in BRITISH_SPELLING.finditer(line):
                report.error(f"{display(path)}:{i + 1}", f"British spelling '{match[0]}'; the register is American")


# --- 7. Container documentation -----------------------------------------------------------

ROLE_LABEL = re.compile(r"\*\*([a-z-]+):\*\*")
LINK_TEXT = re.compile(r"!?\[([^\]]*)\]\([^)]*\)")
DECISION_CELL = re.compile(r"^D(\d+)$")


def plain(cell: str) -> str:
    """A table cell's text without links, bold markers or surrounding space."""
    return LINK_TEXT.sub(r"\1", cell).replace("**", "").strip()


def table_rows(path: Path):
    """Yield (line number, header cells, cells) for each body row of each Markdown table."""
    header = None
    for index, line in unfenced(path.read_text(encoding="utf-8").split("\n")):
        if not line.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
        elif not all(set(cell) <= set("-: ") for cell in cells):
            yield index + 1, header, cells


def check_leader_only(model: Model, report: Report) -> None:
    for element in model.elements.values():
        roles = {role.strip() for role in ((element.get("properties") or {}).get("roles") or "").split(",") if role.strip()}
        tagged = "Leader only" in [tag.strip() for tag in (element.get("tags") or "").split(",")]
        if tagged != (roles == {"leader"}):
            report.error(f"element '{element.get('name')}'", "the Leader only tag and roles 'leader' alone go together")


def check_container_docs(model: Model, layout: "linker.Layout", report: Report) -> None:
    system_id = model.identifiers.get("platform")
    for directory, name in sorted(layout.container_docs.items()):
        container_id = next((i for i, e in model.elements.items()
                             if model.parent.get(i) == system_id and e.get("name") == name), None)
        if container_id is None:
            report.error(display(directory), f"no container named '{name}' in the model")
            continue
        container = model.elements[container_id]
        components = {e["name"]: e for i, e in model.elements.items() if model.parent.get(i) == container_id}

        components_file = directory / "03-components.md"
        if components and components_file.is_file():
            seen = set()
            for number, header, cells in table_rows(components_file):
                component = components.get(plain(cells[0]))
                if component is None:
                    continue
                where = f"{display(components_file)}:{number}"
                seen.add(component["name"])
                description = (component.get("description") or "").strip()
                if len(cells) < 2 or plain(cells[1]) != description:
                    report.error(where, f"the second column must give the model's description of "
                                 f"'{component['name']}': '{description}'")
                if "Actions by role" in header:
                    column = header.index("Actions by role")
                    labels = set(ROLE_LABEL.findall(cells[column] if column < len(cells) else ""))
                    roles = {role.strip() for role in
                             ((component.get("properties") or {}).get("roles") or "").split(",") if role.strip()}
                    if labels != roles:
                        report.error(where, f"actions are given for roles {sorted(labels)}, but "
                                     f"'{component['name']}' has the roles {sorted(roles)}")
            for missing in sorted(set(components) - seen):
                report.error(display(components_file), f"no table row for the component '{missing}'")

        decisions_file = directory / "09-decisions.md"
        if decisions_file.is_file():
            listed = set()
            for _, _, cells in table_rows(decisions_file):
                if match := DECISION_CELL.match(plain(cells[0])):
                    listed.add(int(match[1]))
            expected = set(decision_numbers((container.get("properties") or {}).get("decisions")))
            for number in sorted(expected - listed):
                report.error(display(decisions_file), f"D{number} is in the decisions property of '{name}' but not listed")
            for number in sorted(listed - expected):
                report.error(display(decisions_file), f"D{number} is listed but not in the decisions property of '{name}'")


# --- 8. Deployment routing --------------------------------------------------------------

ROUTED_CLIENTS = ("platform.webApp", "platform.cli", "platform.agent")


def check_deployment_routing(model: Model, report: Report) -> None:
    server = model.identifiers.get("platform.controlPlane")
    clients = {model.identifiers[c] for c in ROUTED_CLIENTS if c in model.identifiers}
    instances: dict[str, list[str]] = {}
    for element_id, element in model.elements.items():
        if element.get("containerId") == server:
            instances.setdefault(element.get("environment"), []).append(element_id)
    for relationship in model.relationships:
        source = model.elements.get(relationship["sourceId"], {})
        destination = model.elements.get(relationship["destinationId"], {})
        environment = destination.get("environment")
        if (source.get("containerId") in clients and destination.get("containerId") == server
                and len(instances.get(environment, [])) > 1):
            node = model.elements.get(model.parent.get(destination["id"]), {}).get("name", "?")
            report.error(f"deployment environment '{environment}'",
                         f"{model.elements[source['containerId']]['name']} connects directly to the control-plane "
                         f"instance in '{node}'; route it through a Service or load balancer, and check the "
                         "deployment groups")


# --- 9. Cut-over --------------------------------------------------------------------------


def check_cutover(root: Path, record: Path, adrs: dict[int, Adr], report: Report) -> None:
    where = "cut-over"
    for number in range(1, CUTOVER_DECISIONS + 1):
        adr = adrs.get(number)
        if adr is None:
            report.error(where, f"D{number} has no ADR")
        elif adr.pending:
            report.error(where, f"D{number} is still pending migration")
    partial = {n for n, a in adrs.items() if a.status == "Partial" and n <= CUTOVER_DECISIONS}
    if partial != CUTOVER_PARTIAL:
        report.error(where, f"Partial decisions are {sorted(partial)}, expected {sorted(CUTOVER_PARTIAL)}")

    workspace_docs = root / "documentation" / "workspace"
    open_items = workspace_docs / "07-open-items.md"
    found = set()
    if open_items.is_file():
        found = {int(n) for n in re.findall(r"^#+ S(\d+)\b", open_items.read_text(encoding="utf-8"), re.M)}
    expected = set(range(1, CUTOVER_OPEN_ITEMS + 1))
    if not expected <= found:
        report.error(where, "open items missing: " + ", ".join(f"S{n}" for n in sorted(expected - found)))

    capabilities: dict[str, set[str]] = {family: set() for family in CUTOVER_CAPABILITIES}
    for path in sorted(workspace_docs.glob("0[3-6]-capabilities-*.md")) if workspace_docs.is_dir() else []:
        for family, number in re.findall(r"\*\*(CORE|DE|DS|MLE) (\d+\.\d+)\*\*", path.read_text(encoding="utf-8")):
            capabilities[family].add(number)
    for family, count in CUTOVER_CAPABILITIES.items():
        if len(capabilities[family]) != count:
            report.error(where, f"{family} has {len(capabilities[family])} capability lines, expected {count}")

    # Reasoning items are carried under their bold title, without the record's number; the
    # titles are read from the record, which still exists when this check runs.
    if not record.is_file():
        report.error(where, f"{display(record)} not found; the reasoning items are read from it")
    else:
        text = record.read_text(encoding="utf-8")
        start = text.index("\n## 3. Key reasoning")
        part = text[start:text.index("\n## 4.", start)]
        items = re.findall(r"^(\d+)\. \*\*(.+?)\*\*", part, re.M)
        if len(items) != CUTOVER_REASONING_ITEMS:
            report.error(where, f"the record has {len(items)} reasoning items, expected {CUTOVER_REASONING_ITEMS}")
        contexts = {}
        for number, adr in adrs.items():
            context = re.search(r"^## Context\n(.*?)(?=^## |\Z)", adr.text, re.M | re.S)
            contexts[number] = context[1] if context else ""
        for item, title in items:
            if int(item) in CUTOVER_DROPPED_REASONING_ITEMS:
                continue
            title = CUTOVER_TITLE_CHANGES.get(int(item), title)
            holders = [f"D{n}" for n, context in sorted(contexts.items()) if f"**{title}**" in context]
            if len(holders) != 1:
                placed = ", ".join(holders) or "no ADR"
                report.error(where, f"reasoning item {item} ('{title}') must be in exactly one Context, found in {placed}")

    # Nothing permanent may refer to the record; the README's migration section is removed with it.
    readme = root.parent / "README.md"
    files = sorted(root.rglob("*.md")) + sorted(root.rglob("*.dsl")) + ([readme] if readme.is_file() else [])
    for path in files:
        text = path.read_text(encoding="utf-8")
        if path == readme:
            start = text.find("\n## Migration from the design record")
            if start != -1:
                end = text.find("\n## ", start + 1)
                text = text[:start] + (text[end:] if end != -1 else "")
        for i, line in enumerate(text.splitlines()):
            match = RECORD_REFERENCE.search(line)
            if match:
                report.error(f"{display(path)}:{i + 1}", f"refers to the design record ('{match[0]}')")


# --- Main ----------------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", type=Path, default=Path("docs/architecture"))
    parser.add_argument("--workspace-json", type=Path, default=Path("docs/build/json/workspace.json"))
    parser.add_argument("--rules", type=Path, default=Path(__file__).with_name("forbidden-edges.json"))
    parser.add_argument("--cutover", action="store_true", help="also run the count check of the cut-over")
    parser.add_argument("--record", type=Path, default=Path("project-design.md"), help="the design record (cut-over only)")
    args = parser.parse_args()

    report = Report()
    decisions_dir = args.root / "decisions"
    adrs = check_adrs(decisions_dir, report)
    have_adrs = decisions_dir.is_dir()

    if args.workspace_json.is_file():
        model = load_model(args.workspace_json)
        check_traceability(model, adrs, have_adrs, report)
        check_forbidden_edges(model, args.rules, adrs, have_adrs, args.cutover, report)
        check_leader_only(model, report)
        check_deployment_routing(model, report)
        check_container_docs(model, linker.Layout(args.root), report)
    else:
        report.error(display(args.workspace_json), "not found; export the workspace as JSON first (make docs-check)")

    check_overlays(args.root, report)
    markdown = sorted(args.root.rglob("*.md"))
    readme = args.root.parent / "README.md"
    if readme.is_file():
        markdown.append(readme)
    check_markdown(markdown, args.root, report)
    check_spelling(args.root.parent, report)
    if args.cutover:
        check_cutover(args.root, args.record, adrs, report)

    for note in report.notes:
        print(f"note: {note}")
    for error in report.errors:
        print(f"error: {error}")
    print(f"docs-check: {len(report.errors)} error(s)")
    return 1 if report.errors else 0


if __name__ == "__main__":
    sys.exit(main())
