"""AST-based schema-template alignment check (Section 0 of test strategy).

Parses Jinja2 user templates and verifies every variable reference exists on its
boundary model. Runs as part of `make check`.

Strategy:
- Walk the Jinja AST collecting Getattr/Getitem nodes
- Extract root variable names from dotted paths (pc.name.tags -> "pc")
- Skip loop variables, filter builtins, macro defs
- For {% include %}, resolve included templates recursively
- Compare extracted roots against boundary model field_names

Phase 1: placeholder contracts pass all checks.
Phase 2: real TEMPLATE_CONTRACTS wired up in tests/test_alignment.py.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import jinja2

from ccya.prompts.context import TEMPLATE_CONTRACTS


_BUILTIN_FILTERS = frozenset({
    "abs", "attr", "batch", "bool", "capitalize", "center", "count", "d",
    "default", "dictsort", "e", "escape", "first", "float", "forceescape",
    "format", "groupby", "indent", "int", "join", "last", "length", "list",
    "lower", "items", "map", "min", "max", "pprint", "random", "reject",
    "rejectattr", "replace", "round", "safe", "select", "selectattr",
    "slice", "sort", "string", "striptags", "sum", "title", "toyaml",
    "trim", "unique", "upper", "urlencode", "urlize", "wordcount",
    "wordwrap", "xmlattr",
})

_CONTROL_FLOW = frozenset({
    # Loop variables are set by these constructs — skip them.
    "for", "if", "elif", "else", "macro", "call", "raw",
})

# Jinja2 builtins and local-set variables that should never be treated as user data fields.
_JINJA_BUILTINS = frozenset({"loop", "namespace"})


def _resolve_include_path(env: jinja2.Environment, template_name: str) -> str | None:
    """Resolve an included template path relative to the prompts directory."""
    templates_dir = Path(__file__).parent.parent / "ccya" / "prompts"

    # Try sections/ subdirectory first (for includes like "sections/_arc.j2")
    for candidate in [template_name, f"sections/{template_name}"]:
        resolved = templates_dir / candidate
        if resolved.exists():
            return str(resolved)

    # Direct path under prompts/
    resolved = templates_dir / template_name
    if resolved.exists():
        return str(resolved)

    return None


def _walk_ast(node: jinja2.nodes.Node):
    """Recursively walk all AST nodes (Jinja 3.x compatible — no .walk() method)."""
    yield node
    for child in node.iter_child_nodes():
        yield from _walk_ast(child)


def _collect_loop_vars(node: jinja2.nodes.Node, vars_out: set[str]):
    """Recursively collect all variable names assigned by a For target."""
    if isinstance(node, jinja2.nodes.Name):
        vars_out.add(node.name)
    elif isinstance(node, jinja2.nodes.Tuple):
        # Jinja 3.x uses .items; older versions used .args.
        items = getattr(node, "items", None) or getattr(node, "args", ())
        for child in items:
            _collect_loop_vars(child, vars_out)


def _get_root(expr: jinja2.nodes.Node, seen: set[str]) -> str | None:
    """Walk Getattr/Getitem chains to find the root variable name."""
    if isinstance(expr, jinja2.nodes.Name):
        return expr.name
    # Jinja 3.x uses .node for the expression; older versions used .expr.
    child = getattr(expr, "node", None) or getattr(expr, "expr", None)
    if child is not None:
        root = _get_root(child, seen)
        if root and root not in seen:
            return root
    # Getitem uses .index for the index expression; check .node too.
    if isinstance(expr, jinja2.nodes.Getitem):
        child = getattr(expr, "node", None) or getattr(expr, "expr", None)
        if child is not None:
            root = _get_root(child, seen)
            if root and root not in seen:
                return root
    return None


def _collect_set_vars(tree: jinja2.nodes.Template) -> set[str]:
    """Collect all variable names assigned by {% set %} in a template."""
    vars_out: set[str] = set()

    def walk(node):
        if isinstance(node, jinja2.nodes.Assign):
            # Assign.target is the Name node being assigned to.
            target = getattr(node, "target", None) or (node.targets[0] if hasattr(node, 'targets') and node.targets else None)  # type: ignore[attr-defined]
            if isinstance(target, jinja2.nodes.Name):
                vars_out.add(target.name)
        for child in node.iter_child_nodes():
            walk(child)

    walk(tree)
    return vars_out


def _extract_roots_from_text(env: jinja2.Environment, text: str) -> set[str]:
    """Parse *text* as a Jinja template and extract root variable names."""
    tree = env.parse(text)
    roots: set[str] = set()
    loop_vars: set[str] = set()

    # Collect local variables from {% set %} — these should be excluded.
    set_vars = _collect_set_vars(tree)

    for node in _walk_ast(tree):
        if isinstance(node, jinja2.nodes.For):
            # Collect loop variables from the target of a For statement.
            _collect_loop_vars(node.target, loop_vars)
            # Also extract root variable name from the iterable (e.g., `for n in npc_roster` -> "npc_roster").
            iter_root = _get_root(node.iter, set())
            if iter_root and iter_root not in loop_vars and iter_root not in _CONTROL_FLOW and iter_root not in _JINJA_BUILTINS and iter_root not in set_vars:
                roots.add(iter_root)
        elif isinstance(node, (jinja2.nodes.Getattr, jinja2.nodes.Getitem)):
            root = _get_root(node, set())
            if root and root not in loop_vars and root not in _CONTROL_FLOW and root not in _JINJA_BUILTINS and root not in set_vars:
                roots.add(root)
        elif isinstance(node, jinja2.nodes.Name):
            # Handle plain Name nodes used directly (e.g., {{ user_input }}).
            name = node.name if hasattr(node, 'name') else ''
            if name and name not in loop_vars and name not in _CONTROL_FLOW and name not in _JINJA_BUILTINS and name not in set_vars:
                roots.add(name)

    return roots


def extract_roots_from_template(
    env: jinja2.Environment, template_path: str | Path
) -> set[str]:
    """Extract all root variable names used by a Jinja template (including includes)."""
    text = Path(template_path).read_text()
    tree = env.parse(text)

    # First pass: collect include nodes and their resolved paths.
    included_roots: set[str] = set()
    for node in _walk_ast(tree):
        if isinstance(node, jinja2.nodes.Include):
            inc_name = _resolve_include(node, env)
            if inc_name:
                inc_roots = extract_roots_from_template(env, inc_name)
                included_roots |= inc_roots

    # Second pass: collect direct variable references in this template.
    text_roots = _extract_roots_from_text(env, text)

    return included_roots | text_roots


def _resolve_include(node: jinja2.nodes.Include, env: jinja2.Environment) -> str | None:
    """Resolve an Include AST node to a filesystem path."""
    template_name_node = node.template
    if isinstance(template_name_node, jinja2.nodes.Const):
        name = template_name_node.value  # type: ignore[attr-defined]
    elif isinstance(template_name_node, (jinja2.nodes.Add,)):
        # Handle string concatenation in include expressions.
        left = _get_const_string(template_name_node.left)  # type: ignore[arg-type]
        right = _get_const_string(template_name_node.right)  # type: ignore[arg-type]
        if left is not None and right is not None:
            name = left + right
        else:
            return None
    else:
        return None

    return _resolve_include_path(env, str(name))


def _get_const_string(node: Any) -> str | None:
    """Extract a constant string from an AST node."""
    if isinstance(node, jinja2.nodes.Const):
        return node.value  # type: ignore[attr-defined]
    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def _make_env() -> jinja2.Environment:
    """Create a Jinja env with the prompts directory as loader."""
    templates_dir = Path(__file__).parent.parent / "ccya" / "prompts"
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(templates_dir)),
        undefined=jinja2.StrictUndefined,
    )


def _check_alignment(template_name: str) -> tuple[set[str], set[str]]:
    """Return (missing_from_schema, dead_fields) for a template."""
    env = _make_env()

    # Find the actual template file.
    templates_dir = Path(__file__).parent.parent / "ccya" / "prompts"
    candidate = templates_dir / template_name
    if not candidate.exists():
        raise FileNotFoundError(f"Template {template_name} not found at {candidate}")

    roots = extract_roots_from_template(env, str(candidate))

    # Get boundary model field names.
    contract_cls = TEMPLATE_CONTRACTS.get(template_name)
    if contract_cls is None:
        return set(), set()  # No contract defined — skip check.

    schema_fields = contract_cls.model_fields

    missing_from_schema = roots - schema_fields.keys()
    dead_fields = schema_fields.keys() - roots

    return missing_from_schema, dead_fields


def _test_alignment(template_name: str) -> None:
    """Generic alignment test for a single template."""
    missing, dead = _check_alignment(template_name)

    if missing:
        raise AssertionError(
            f"{template_name}: variables not found on boundary model: "
            f"{sorted(missing)}"
        )


def test_storytell_user_alignment() -> None:
    """All root variables in storytell_user.j2 exist on StorytellerBoundary."""
    _test_alignment("storytell_user.j2")


def test_narrate_user_alignment() -> None:
    """All root variables in narrate_user.j2 exist on NarratorBoundary."""
    _test_alignment("narrate_user.j2")


def test_rules_user_alignment() -> None:
    """All root variables in rules_user.j2 exist on RulesBoundary."""
    _test_alignment("rules_user.j2")


def test_scene_extract_user_alignment() -> None:
    """All root variables in extract_scene_user.j2 exist on SceneExtractBoundary."""
    _test_alignment("extract_scene_user.j2")


def test_state_extract_user_alignment() -> None:
    """All root variables in extract_state_user.j2 exist on StateExtractBoundary."""
    _test_alignment("extract_state_user.j2")


def test_narrate_system_alignment() -> None:
    """All root variables in narrate_system.j2 exist on NarratorSystemBoundary."""
    _test_alignment("narrate_system.j2")
