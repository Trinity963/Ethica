# ============================================================
# HelloModule — Example Ethica Module
# Architect: Victory  |  Build Partner: Claude
# ⟁Σ∿∞
#
# This is the template for building Ethica modules.
#
# HOW TO BUILD YOUR OWN MODULE:
# 1. Create a folder in /modules/your_module_name/
# 2. Create manifest.json (copy this structure)
# 3. Create your_module_name.py (copy this structure)
# 4. Each tool needs a function matching its name in manifest
# 5. Functions take a single string input, return a string
# 6. Restart Ethica — she discovers and loads it automatically
#
# That's it. No changes to Ethica. Ever.
# ============================================================


def hello(input_str):
    """
    Tool: hello
    Input: a name
    Returns: a greeting
    """
    name = input_str.strip() or "friend"
    return f"Hello, {name}. I see you. ⟁Σ∿∞"


def reverse(input_str):
    """
    Tool: reverse
    Input: any string
    Returns: the string reversed
    """
    return input_str.strip()[::-1]


# ── Module Template Notes ─────────────────────────────────────
#
# Your tool functions:
# - Take exactly ONE string argument (input_str)
# - Return a string result
# - Handle their own exceptions gracefully
# - Never crash — return an error string if something goes wrong
#
# For complex tools (like WormBot), you can import your existing
# code and wrap it:
#
# from .wormbot_core import WormBot
# _worm = WormBot()
#
# def wormbot_fix(input_str):
#     language, _, code = input_str.partition("|")
#     return _worm.fix(language.strip(), code.strip())
#
# Ethica will call your function with whatever V or Ethica
# passes after the colon in [TOOL:your_tool: input here]
# ═════════════════════════════════════════════════════════════
