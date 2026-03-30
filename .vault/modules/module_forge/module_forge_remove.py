# ── REMOVE TOOL — appended to module_forge.py ────────────────

_remove_win = None


def _open_remove(root_widget, registry):
    global _remove_win
    if _remove_win and _remove_win.winfo_exists():
        _remove_win.lift()
        return

    win = tk.Toplevel(root_widget)
    _remove_win = win
    win.title("⬡  ModuleForge — Remove a Module")
    win.configure(bg=BG)
    win.geometry("500x420")
    win.resizable(False, True)

    tk.Label(win, text="⬡  REMOVE MODULE", bg=BG, fg=RED,
             font=("Courier New", 12, "bold")).pack(pady=(16, 2))
    tk.Label(win, text="Select a forge-built module to uninstall.",
             bg=BG, fg=TEXT_DIM,
             font=("Courier New", 8)).pack(pady=(0, 8))
    tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)

    status_var = tk.StringVar(value="")
    status_label = tk.Label(win, textvariable=status_var, bg=BG,
                             fg=GREEN, font=("Courier New", 8), wraplength=460)

    list_frame = tk.Frame(win, bg=BG)
    list_frame.pack(fill="both", expand=True, padx=16, pady=8)

    def _refresh_list():
        for w in list_frame.winfo_children():
            w.destroy()

        # Find forge-built modules from chat_engine.py tags
        forge_modules = _find_forge_modules()

        if not forge_modules:
            tk.Label(list_frame, text="No forge-built modules found.",
                     bg=BG, fg=TEXT_DIM,
                     font=("Courier New", 9)).pack(pady=20)
            return

        for mod in forge_modules:
            card = tk.Frame(list_frame, bg=BG_PANEL, pady=6, padx=10)
            card.pack(fill="x", pady=4)

            tk.Label(card, text=f"⬡  {mod['folder']}", bg=BG_PANEL, fg=CYAN,
                     font=("Courier New", 9, "bold")).pack(side="left")

            tools_text = ", ".join(mod['triggers'])
            tk.Label(card, text=f"  [{tools_text}]", bg=BG_PANEL, fg=TEXT_DIM,
                     font=("Courier New", 7)).pack(side="left")

            def _make_remove(m):
                def _do():
                    ok, msg = _remove_module(m, registry)
                    status_var.set(msg)
                    status_label.config(fg=GREEN if ok else RED)
                    _refresh_list()
                return _do

            tk.Button(card, text="✕ REMOVE", bg=BG_CARD, fg=RED,
                      font=("Courier New", 7, "bold"), relief="flat",
                      padx=6, pady=2, cursor="hand2",
                      command=_make_remove(mod)).pack(side="right")

    _refresh_list()

    status_label.pack(padx=20, pady=4)
    tk.Frame(win, bg=BORDER, height=1).pack(fill="x", padx=16, pady=4)
    tk.Button(win, text="↺  REFRESH", bg=BG_CARD, fg=CYAN,
              font=("Courier New", 8, "bold"), relief="flat",
              padx=8, pady=4, cursor="hand2",
              command=_refresh_list).pack(pady=(0, 12))


def _find_forge_modules():
    """
    Scan chat_engine.py for # ModuleForge tagged lines.
    Returns list of dicts: {folder, triggers, tool_names}
    Excludes forge_open and build_module (ModuleForge's own triggers).
    """
    BUILTIN = {"forge_open", "forge_remove"}
    BUILTIN_TRIGGERS = {"forge module", "build module", "remove module"}

    try:
        content = ENGINE_PATH.read_text()
    except Exception:
        return []

    modules = {}
    for line in content.splitlines():
        if "# ModuleForge" not in line:
            continue
        # Parse lines like: "trigger phrase": ("tool_name", ...), # ModuleForge
        import re
        m = re.search(r'"([^"]+)"\s*:\s*\("([^"]+)"', line)
        if not m:
            # Also handle flat trigger list: "trigger",  # ModuleForge
            m2 = re.search(r'"([^"]+)"', line)
            if m2:
                trig = m2.group(1)
                if trig not in BUILTIN_TRIGGERS:
                    # Try to find folder from modules dir
                    folder = _guess_folder(trig)
                    if folder and folder not in modules:
                        modules[folder] = {"folder": folder, "triggers": [trig], "tool_names": []}
                    elif folder:
                        modules[folder]["triggers"].append(trig)
            continue

        trig = m.group(1)
        tool = m.group(2)
        if trig in BUILTIN_TRIGGERS or tool in BUILTIN:
            continue
        folder = _guess_folder(trig)
        if not folder:
            continue
        if folder not in modules:
            modules[folder] = {"folder": folder, "triggers": [trig], "tool_names": [tool]}
        else:
            if trig not in modules[folder]["triggers"]:
                modules[folder]["triggers"].append(trig)
            if tool not in modules[folder]["tool_names"]:
                modules[folder]["tool_names"].append(tool)

    return list(modules.values())


def _guess_folder(trigger):
    """Map a trigger phrase to a module folder name."""
    # Check all module folders for a manifest whose tools match
    try:
        for folder in MODULES_DIR.iterdir():
            if not folder.is_dir():
                continue
            manifest_path = folder / "manifest.json"
            if not manifest_path.exists():
                continue
            try:
                manifest = json.loads(manifest_path.read_text())
                for tool in manifest.get("tools", []):
                    if tool.get("example", "").lower() == trigger.lower():
                        return folder.name
                    if trigger.replace(" ", "_") in tool.get("name", ""):
                        return folder.name
            except Exception:
                continue
        # Fallback: slugify trigger and check if folder exists
        slug = _slugify(trigger.split()[0]) + "_module"
        if (MODULES_DIR / slug).exists():
            return slug
    except Exception:
        pass
    return None


def _remove_module(mod, registry):
    """
    Full removal pipeline:
    1. Strip # ModuleForge tagged lines from chat_engine.py
    2. Hot-deregister from registry
    3. Delete module folder
    """
    import shutil

    # ── 1. Strip from chat_engine.py ─────────────────────────
    try:
        content = ENGINE_PATH.read_text()
        lines = content.splitlines(keepends=True)
        # Remove lines tagged # ModuleForge that match this module's triggers/tools
        triggers_set = set(mod["triggers"])
        tools_set = set(mod.get("tool_names", []))
        new_lines = []
        for line in lines:
            if "# ModuleForge" not in line:
                new_lines.append(line)
                continue
            import re
            m = re.search(r'"([^"]+)"\s*:\s*\("([^"]+)"', line)
            if m:
                trig, tool = m.group(1), m.group(2)
                if trig in triggers_set or tool in tools_set:
                    continue  # drop this line
            else:
                # flat trigger list entry
                m2 = re.search(r'"([^"]+)"', line)
                if m2 and m2.group(1) in triggers_set:
                    continue
            new_lines.append(line)

        new_content = "".join(new_lines)
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return False, f"Syntax error after strip: {e}"
        ENGINE_PATH.write_text(new_content)
    except Exception as e:
        return False, f"Failed to patch chat_engine.py: {e}"

    # ── 2. Hot-deregister ─────────────────────────────────────
    if registry:
        try:
            folder_path = str(MODULES_DIR / mod["folder"])
            folder_name = mod["folder"]
            existing = [k for k in registry._modules
                        if folder_name.lower() in k.lower() or k.lower() in folder_name.lower()]
            for k in existing:
                m_obj = registry._modules.pop(k, None)
                if m_obj:
                    for tool in m_obj.tools:
                        registry._tool_index.pop(tool.name.lower(), None)
        except Exception as e:
            pass  # deregister best-effort

    # ── 3. Delete folder ──────────────────────────────────────
    try:
        folder = MODULES_DIR / mod["folder"]
        if folder.exists():
            shutil.rmtree(folder)
    except Exception as e:
        return False, f"Folder delete failed: {e}"

    return True, f"✓ {mod['folder']} removed — triggers cleared, folder deleted."


def forge_remove(input_str):
    """
    Tool: forge_remove
    Trigger: remove module
    Opens the ModuleForge removal UI.
    """
    import tkinter as tk
    registry = None
    try:
        root = tk._default_root
        if root and hasattr(root, "engine") and hasattr(root.engine, "modules"):
            registry = root.engine.modules
    except Exception:
        pass
    try:
        root = tk._default_root
        root.after(0, lambda: _open_remove(root, registry))
    except Exception as e:
        return f"ModuleForge remove error: {e}"
    return "Opening ModuleForge Remove… ⬡"
