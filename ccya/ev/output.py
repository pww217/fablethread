from __future__ import annotations

import re
from typing import Any

SECTION_MARKERS: dict[str, str] = {
    "campaign_arc": r"^#{1,3}\s*Campaign Arc$",
    "rules_outcome": r"^## rules_outcome$",
    "pacing_context": r"^## pacing_context$",
    "player_intent": r"^## player_intent$",
    "threads": r"^## threads",
    "last_turn_narration": r"^## last_turn_narration",
    "current_narration": r"^## CURRENT TURN",
    "end_narration": r"^## END CURRENT TURN",
    "characters": r"^## characters$",
    "location": r"^## location$",
    "inventory": r"^## Current inventory",
}

_COMPILED_SECTIONS: dict[str, re.Pattern[str]] = {
    name: re.compile(pattern) for name, pattern in SECTION_MARKERS.items()
}


def extract_section_by_pattern(text: str | None, start_name: str, *stop_names: str) -> str:
    if not text or start_name not in _COMPILED_SECTIONS:
        return ""
    start_re = _COMPILED_SECTIONS[start_name]
    stop_re_list = [_COMPILED_SECTIONS.get(s) for s in stop_names if s in _COMPILED_SECTIONS]

    lines = text.splitlines()
    found = False
    result: list[str] = []
    for line in lines:
        stripped = line.strip()
        if found:
            if any(r.search(stripped) for r in stop_re_list if r):
                break
            if stripped.startswith("#") and not any(r.search(stripped) for r in stop_re_list if r):
                continue
            if stripped:
                result.append(line)
        elif start_re.search(stripped):
            found = True
    return "\n".join(result).strip()


def _dict_to_lines(d: dict[str, Any], max_str: int = 150) -> list[dict[str, Any]]:
    lines = []
    for k, v in d.items():
        if v is None:
            lines.append({"k": k, "v": "null", "dim": True})
        elif isinstance(v, bool):
            lines.append({"k": k, "v": str(v).lower(), "dim": not v})
        elif isinstance(v, list):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            elif all(isinstance(x, (str, int, float)) for x in v):
                joined = ", ".join(str(x) for x in v)
                lines.append({"k": k, "v": joined[:max_str] + ("\u2026" if len(joined) > max_str else "")})
            elif all(isinstance(x, dict) for x in v):
                labels = []
                for x in v:
                    for key in ("id", "name", "text", "label"):
                        val = x.get(key)
                        if val and isinstance(val, str):
                            labels.append(val[:60])
                            break
                summary = ", ".join(lbl for lbl in labels if lbl)
                display = f"[{len(v)}] {summary}" if summary else f"[{len(v)}]"
                lines.append({"k": k, "v": display[:max_str]})
            else:
                lines.append({"k": k, "v": f"[{len(v)} items]"})
        elif isinstance(v, dict):
            if not v:
                lines.append({"k": k, "v": "\u2205", "dim": True})
            else:
                for sk, sv in v.items():
                    sub_k = f"{k}.{sk}"
                    if sv is None:
                        lines.append({"k": sub_k, "v": "null", "dim": True})
                    elif isinstance(sv, str):
                        lines.append({"k": sub_k, "v": sv[:max_str] + ("\u2026" if len(sv) > max_str else "")})
                    else:
                        lines.append({"k": sub_k, "v": str(sv)[:max_str]})
        elif isinstance(v, str):
            lines.append({"k": k, "v": v[:max_str] + ("\u2026" if len(v) > max_str else "")})
        else:
            lines.append({"k": k, "v": str(v)})
    return lines


def _wrap_text(text: str, indent: int = 0) -> list[str]:
    import textwrap

    lines = []
    for para in text.splitlines():
        wrapped = textwrap.fill(para.strip(), width=80 - indent if indent else 80, initial_indent=" " * indent, subsequent_indent=" " * indent) if para.strip() else ""
        if wrapped:
            lines.append(wrapped)
    return lines


def _shorten(value: Any) -> str:
    if isinstance(value, dict):
        keys = list(value.keys())[:3]
        rest = f" (+{len(value) - 3} more)" if len(value) > 3 else ""
        return "{" + ", ".join(str(k) for k in keys) + "}" + rest
    elif isinstance(value, list):
        if not value:
            return "[]"
        first = str(value[0])[:80]
        rest = f" (+{len(value) - 1} more)" if len(value) > 1 else ""
        return f"[{first}{rest}]"
    elif isinstance(value, str):
        return value[:200] + ("\u2026" if len(value) > 200 else "")
    else:
        return str(value)[:200]


def _shorten_value(value: str) -> str:
    if len(value) > 60:
        return value[:57] + "\u2026"
    return value


def _short_item_name(name: str) -> str:
    words = name.split()
    if not words:
        return "?"
    if len(name) <= 15:
        return name[:20]
    abbr = "".join(w[0].upper() for w in words if w)
    if len(words) > 2:
        return abbr + name[-3:]
    return abbr[:6]


def _values_equal(a: Any, b: Any) -> bool:
    if a is None and b is None:
        return True
    if a is None or b is None:
        return False
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return False
        for i in range(len(a)):
            ai = a[i] if isinstance(a[i], dict) else {"id": str(a[i])}
            bi = b[i] if isinstance(b[i], dict) else {"id": str(b[i])}
            if ai.get("id") != bi.get("id"):
                return False
        return True
    return bool(a == b)


def _describe_collection_change(prev: Any, curr: Any) -> list[str]:
    changes = []

    def _item_map(items: Any) -> dict[str, dict[str, Any]]:
        m: dict[str, dict[str, Any]] = {}
        for item in items:
            if isinstance(item, dict):
                iid = item.get("id", "")
                if iid and isinstance(iid, str):
                    m[iid] = item
            elif isinstance(item, str):
                m[item] = {"id": item}
        return m

    pm = _item_map(prev) if prev else {}
    cm = _item_map(curr) if curr else {}

    for iid in sorted(set(pm.keys()) | set(cm.keys())):
        if iid not in pm and iid in cm:
            name = (cm[iid].get("name", "") or "")[:20]
            changes.append(f"+{iid} {name}")
        elif iid in pm and iid not in cm:
            name = (pm[iid].get("name", "") or "")[:20]
            changes.append(f"-{iid} {name}")

    return changes


def _trace_display_name(field: str) -> str:
    if field == "inventory":
        return "Inventory"
    elif field.startswith("inventory."):
        item_id = field[len("inventory."):]
        return f"Item {item_id}"
    elif field == "conditions":
        return "Conditions"
    elif field.startswith("conditions."):
        cond_id = field[len("conditions."):]
        return f"Condition {cond_id}"
    elif field == "npcs":
        return "NPCs Present"
    elif field.startswith("npcs."):
        npc_id = field[len("npcs."):]
        return f"NPC {npc_id}"
    elif field == "location":
        return "Location"
    elif field == "scene.tags":
        return "Scene Tags"
    elif field == "scene.tagline":
        return "Tagline"
    else:
        return field


def format_trace_value(value: Any, field: str) -> str:
    if value is None:
        return "(no data)"

    if isinstance(value, list):
        if not value:
            return "(empty)"
        if field == "inventory":
            parts = []
            for item in sorted(value, key=lambda x: ("0" if isinstance(x, dict) and x.get("id") == "credits" else "1", (x.get("name") or "").lower())):
                if not isinstance(item, dict):
                    continue
                name = _short_item_name(str(item.get("name", item.get("id", "?"))))
                amt = int((item.get("amount") or 1))
                parts.append(f"{name}\u00d7{amt}")
            return ", ".join(parts) if parts else "(empty)"

        elif field == "conditions":
            labels = []
            for c in value:
                if isinstance(c, dict):
                    lbl = c.get("label", "") or c.get("id", "?")
                    labels.append(lbl)
                else:
                    labels.append(str(c))
            return ", ".join(labels) if labels else "(empty)"

        elif field == "npcs":
            if isinstance(value, list):
                return ", ".join(str(n) for n in value if value) if value else "(empty)"
            return str(value)

        items = [str(x)[:40] for x in value[:10]]
        result = ", ".join(items)
        if len(value) > 10:
            result += f" (+{len(value)-10} more)"
        return result

    elif isinstance(value, dict):
        name = value.get("name", "") or ""
        npc_id = value.get("id", "?")
        if name:
            return f"{npc_id}: {name}"
        return str({k: v for k, v in list(value.items())[:3]})

    elif isinstance(value, str):
        return value[:100] + ("\u2026" if len(value) > 100 else "")

    return str(value)[:200]
