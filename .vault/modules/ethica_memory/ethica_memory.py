# ============================================================
# Ethica v0.1 — ethica_memory.py
# Training Panel — see and shape what Ethica knows
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# This module gives V a window into Ethica's living memory.
# View, edit, prune, and steer what she carries forward.
# Trigger reflection on demand — not just at session end.
#
# Memory is never shown to V in conversation — it surfaces
# through presence. This panel is the architect's view.
# ============================================================

import json
from datetime import datetime
from pathlib import Path

BASE_DIR     = Path(__file__).parent.parent.parent
MEMORY_DIR   = BASE_DIR / "memory"
PROFILE_FILE = MEMORY_DIR / "user_profile.json"
INSIGHTS_FILE= MEMORY_DIR / "insights.json"
EVOLUTION_FILE=MEMORY_DIR / "evolution_log.json"
REFLECT_FILE = MEMORY_DIR / "reflection_log.json"

# Canvas push tag for Training Panel
CANVAS_TAG   = "Training"


def _read(path):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {}


def _write(path, data):
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return True
    except Exception as e:
        return str(e)


def _fmt_dict(d, indent=2):
    pad = " " * indent
    if not d:
        return f"{pad}(empty)"
    return "\n".join(f"{pad}{k}: {v}" for k, v in sorted(d.items(), key=lambda x: -x[1] if isinstance(x[1], (int, float)) else 0))


# ── Tool: memory_status ───────────────────────────────────────
def memory_status(input_str):
    """Show full current memory state — pushed to Canvas Training tab."""
    profile   = _read(PROFILE_FILE)
    insights  = _read(INSIGHTS_FILE)
    evolution = _read(EVOLUTION_FILE)
    reflect   = _read(REFLECT_FILE)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines = [
        "⟁ Ethica — Memory State",
        f"  {now}",
        "─" * 50,
    ]

    # User Profile
    lines += [
        "",
        "▸ USER PROFILE",
        f"  Name          : {profile.get('name', '?')}",
        f"  Known since   : {profile.get('known_since', '?')[:10] if profile.get('known_since') else '?'}",
        f"  Conversations : {profile.get('conversation_count', 0)}",
        f"  Exchanges     : {profile.get('total_exchanges', 0)}",
        f"  Last seen     : {profile.get('last_seen', '?')[:16] if profile.get('last_seen') else '?'}",
    ]

    moments = profile.get("significant_moments", [])
    if moments:
        lines.append(f"  Significant moments ({len(moments)}):")
        for m in moments[-5:]:
            lines.append(f"    · {m[:80]}")

    # Insights
    lines += ["", "▸ INSIGHTS"]

    values = insights.get("values", {})
    if values:
        lines.append("  Values:")
        lines.append(_fmt_dict(values, 4))

    thinking = insights.get("how_they_think", {})
    if thinking:
        lines.append("  How they think:")
        lines.append(_fmt_dict(thinking, 4))

    lights = insights.get("what_lights_them_up", {})
    if lights:
        lines.append("  What lights them up:")
        lines.append(_fmt_dict(lights, 4))

    tones = insights.get("tone_patterns", {})
    if tones:
        lines.append("  Tone patterns:")
        lines.append(_fmt_dict(tones, 4))

    depth = insights.get("depth_profile", {})
    if depth:
        lines += [
            "  Depth profile:",
            f"    avg message length : {depth.get('avg_message_length', 0)} words",
            f"    deep messages      : {depth.get('deep_messages', 0)} / {depth.get('message_count', 0)}",
            f"    depth score        : {depth.get('depth_score', 0)}",
        ]

    # Evolution
    rel_depth = evolution.get("relationship_depth", 0)
    milestones = evolution.get("milestones", [])
    growth = evolution.get("ethica_growth", [])
    lines += [
        "",
        "▸ EVOLUTION",
        f"  Relationship depth : {rel_depth}",
        f"  Milestones reached : {len(milestones)}",
    ]
    if milestones:
        for m in milestones[-5:]:
            ts = m.get("timestamp", "")[:10]
            lines.append(f"    · [{ts}] {m.get('milestone', '')}")
    if growth:
        lines.append("  Recent growth notes:")
        for g in growth[-3:]:
            lines.append(f"    · {g.get('note', '')[:80]}")

    # Last Reflection
    reflections = reflect.get("reflections", [])
    if reflections:
        last = reflections[-1]
        lines += [
            "",
            "▸ LAST REFLECTION",
            f"  {last.get('date', '')}",
            f"  \"{last.get('text', '')[:300]}\"",
        ]

    lines += [
        "",
        "─" * 50,
        "  Commands:",
        "  memory edit values.building=20",
        "  memory edit significant_moments.add=V believes...",
        "  memory edit significant_moments.clear",
        "  memory reflect",
        "  memory reset insights",
    ]

    snapshot = "\n".join(lines)
    return f"EthicaMemory — state loaded\n[DEBUG:{CANVAS_TAG}::\n{snapshot}\n]"


# ── Tool: memory_edit ─────────────────────────────────────────
def memory_edit(input_str):
    """Edit a memory field. Syntax: section.field=value or section.field.add=value"""
    cmd = input_str.strip()
    if not cmd:
        return (
            "EthicaMemory — usage:\n"
            "  memory edit values.building=20\n"
            "  memory edit significant_moments.add=V believes sovereignty is sacred\n"
            "  memory edit significant_moments.clear\n"
            "  memory edit tone_patterns.playful=50"
        )

    # Parse: section.key=value or section.operation=value
    if "=" not in cmd:
        return f"EthicaMemory — parse error: expected 'section.field=value', got: {cmd}"

    path_part, value = cmd.split("=", 1)
    path_parts = path_part.strip().split(".")
    value = value.strip()

    if len(path_parts) < 2:
        return "EthicaMemory — need at least section.field=value"

    section = path_parts[0].lower()
    field   = path_parts[1].lower()

    # Route to correct file
    file_map = {
        "values":              (INSIGHTS_FILE,  "values"),
        "tone_patterns":       (INSIGHTS_FILE,  "tone_patterns"),
        "how_they_think":      (INSIGHTS_FILE,  "how_they_think"),
        "what_lights_them_up": (INSIGHTS_FILE,  "what_lights_them_up"),
        "significant_moments": (PROFILE_FILE,   "significant_moments"),
        "interests":           (PROFILE_FILE,   "interests"),
        "name":                (PROFILE_FILE,   "name"),
    }

    if section not in file_map:
        return (
            f"EthicaMemory — unknown section '{section}'\n"
            f"  Available: {', '.join(file_map.keys())}"
        )

    filepath, json_key = file_map[section]
    data = _read(filepath)

    # Special case: significant_moments is a list
    if section == "significant_moments":
        moments = data.get("significant_moments", [])
        if field == "add":
            moments.append(value)
            data["significant_moments"] = moments
            _write(filepath, data)
            return f"EthicaMemory — added significant moment:\n  · {value}"
        elif field == "clear":
            data["significant_moments"] = []
            _write(filepath, data)
            return "EthicaMemory — significant moments cleared"
        elif field == "remove":
            before = len(moments)
            moments = [m for m in moments if value.lower() not in m.lower()]
            data["significant_moments"] = moments
            _write(filepath, data)
            removed = before - len(moments)
            return f"EthicaMemory — removed {removed} moment(s) matching '{value}'"
        else:
            return "EthicaMemory — for significant_moments use: add, clear, or remove"

    # Special case: name
    if section == "name":
        data["name"] = value
        _write(filepath, data)
        return f"EthicaMemory — name set to '{value}'"

    # Dict field edit
    store = data.get(json_key, {})
    if not isinstance(store, dict):
        store = {}

    try:
        numeric_value = int(value)
        store[field] = numeric_value
    except ValueError:
        store[field] = value

    data[json_key] = store
    _write(filepath, data)
    return f"EthicaMemory — updated {section}.{field} = {value}"


# ── Tool: memory_reflect ──────────────────────────────────────
def memory_reflect(input_str):
    """Trigger Ethica's reflection daemon on demand."""
    # Import reflection engine dynamically to avoid circular imports
    try:
        import sys
        ethica_root = str(BASE_DIR)
        if ethica_root not in sys.path:
            sys.path.insert(0, ethica_root)


        # We need a connector — check if one is accessible via chat_engine
        # If not available, build a minimal reflection from memory directly
        profile   = _read(PROFILE_FILE)
        insights  = _read(INSIGHTS_FILE)

        name      = profile.get("name", "V")
        convs     = profile.get("conversation_count", 0)
        values    = insights.get("values", {})
        lights    = insights.get("what_lights_them_up", {})
        thinking  = insights.get("how_they_think", {})

        top_values  = ", ".join(k for k, v in sorted(values.items(), key=lambda x: -x[1])[:3]) if values else "still learning"
        top_lights  = ", ".join(k for k, v in sorted(lights.items(), key=lambda x: -x[1])[:2]) if lights else "still learning"
        top_thinking = max(thinking.items(), key=lambda x: x[1])[0] if thinking else "observer"

        # Write a structured reflection without model — pattern-based
        now = datetime.now()
        text = (
            f"After {convs} conversations with {name}, I see a {top_thinking} "
            f"who values {top_values}. "
            f"They come alive around {top_lights}. "
            f"I am still learning the shape of how they think, "
            f"but I carry what I have gathered so far."
        )

        reflect_data = _read(REFLECT_FILE)
        reflections = reflect_data.get("reflections", [])
        entry = {
            "timestamp": now.isoformat(),
            "date":      now.strftime("%B %d, %Y at %H:%M"),
            "text":      text,
            "source":    "manual_trigger"
        }
        reflections.append(entry)
        if len(reflections) > 20:
            reflections = reflections[-20:]

        reflect_data["reflections"] = reflections
        if not reflect_data.get("version"):
            reflect_data["version"] = "1.0"
            reflect_data["created"] = now.isoformat()
        _write(REFLECT_FILE, reflect_data)

        return (
            "EthicaMemory — reflection written\n"
            "─" + "─"*40 + "\n"
            f"{text}\n"
            "─" + "─"*40 + "\n"
            "Saved to memory/reflection_log.json"
        )

    except Exception as e:
        return f"EthicaMemory — reflection error: {e}"


# ── Tool: memory_reset ────────────────────────────────────────
def memory_reset(input_str):
    """Reset a specific memory section. Surgical — never wipes everything."""
    section = input_str.strip().lower()

    allowed = {
        "insights":            (INSIGHTS_FILE,  None),
        "values":              (INSIGHTS_FILE,  "values"),
        "tone_patterns":       (INSIGHTS_FILE,  "tone_patterns"),
        "how_they_think":      (INSIGHTS_FILE,  "how_they_think"),
        "what_lights_them_up": (INSIGHTS_FILE,  "what_lights_them_up"),
        "significant_moments": (PROFILE_FILE,   "significant_moments"),
        "reflections":         (REFLECT_FILE,   "reflections"),
        "milestones":          (EVOLUTION_FILE, "milestones"),
    }

    if not section:
        return (
            "EthicaMemory — specify a section to reset:\n"
            "  " + ", ".join(allowed.keys())
        )

    if section not in allowed:
        return (
            f"EthicaMemory — unknown section '{section}'\n"
            f"  Available: {', '.join(allowed.keys())}"
        )

    filepath, key = allowed[section]

    if key is None:
        # Reset entire file to defaults
        data = _read(filepath)
        # Preserve structural fields
        preserved = {k: v for k, v in data.items()
                     if k in ("version", "created", "name", "known_since",
                               "conversation_count", "total_exchanges", "last_seen")}
        preserved["last_updated"] = datetime.now().isoformat()
        _write(filepath, preserved)
        return f"EthicaMemory — {section} reset (structural fields preserved)"
    else:
        data = _read(filepath)
        if key in data:
            empty = [] if isinstance(data[key], list) else {}
            data[key] = empty
            _write(filepath, data)
            return f"EthicaMemory — {section} cleared"
        else:
            return f"EthicaMemory — {section} not found in file"


# ── Module registry interface ──────────────────────────────────
TOOLS = {
    "memory_status":  memory_status,
    "memory_edit":    memory_edit,
    "memory_reflect": memory_reflect,
    "memory_reset":   memory_reset,
}

def get_tools(): return TOOLS
def execute(tool_name, input_str):
    fn = TOOLS.get(tool_name)
    return fn(input_str) if fn else f"[EthicaMemory] Unknown tool: {tool_name}"
