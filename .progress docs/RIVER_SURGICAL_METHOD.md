# RIVER'S SURGICAL IMPLANTATION GUIDE
### How to read, locate, and patch code without ever touching what works
**Architect**: Victory — The Architect  
**Method**: River (Claude)  
**Glyph**: ⟁Σ∿∞

---

## The Prime Directive

> **Surgical over wholesale. Always.**

Large codebases are living systems. Files like `chat_engine.py`,
`main_window.py`, `dashboard_ui.py` can be 800–1000+ lines deep.
Rewriting them from scratch is how you break working things.

The surgical method: **locate → read → patch → verify**.
Never more. Never less.

---

## THE FOUR TOOLS

### 1. `grep -n` — The Locator

Find exactly where something lives. Line numbers always.

```bash
# Find a function definition
grep -n "def _build_agent_ops" ~/Ethica/modules/kernel/dashboard_ui.py

# Find all references to a pattern across a file
grep -n "AGENTS\|agent_list" ~/Ethica/modules/kernel/kernel.py

# Find across multiple files
grep -rn "OPEN_DASHBOARD" ~/Ethica/ui/

# Pipe to head when you expect many results
grep -n "def " ~/Ethica/core/chat_engine.py | head -20
```

**Rule**: Never assume where something is. Grep first.  
**Rule**: Always use `-n` — line numbers are your map.

---

### 2. `sed -n` — The Precision Reader

Once grep gives you a line number, read the exact context around it.
Never paste full files. Never guess at surrounding code.

```bash
# Read lines 224 to 310 — see the full function
sed -n '224,310p' ~/Ethica/modules/kernel/dashboard_ui.py

# Read 10 lines around a known line (e.g. line 95)
sed -n '90,105p' ~/Ethica/core/chat_engine.py

# Combine with grep: find line, then read around it
grep -n "AGENTS" ~/Ethica/modules/kernel/kernel.py
# → 16: AGENTS = ["river", "gage", "reka"]
sed -n '14,20p' ~/Ethica/modules/kernel/kernel.py
```

**Rule**: Read ±10 lines around your target before patching.  
**Rule**: Never write a patch without having read the exact bytes.

---

### 3. `python3` string replace — The Surgeon

The actual implantation. Match the exact string, replace only that,
verify the file is syntactically clean after every write.

```python
python3 << 'EOF'
with open('/home/trinity/Ethica/modules/kernel/kernel.py', 'r') as f:
    content = f.read()

# The old string — must match EXACTLY, character for character
old = 'AGENTS = ["river", "gage", "reka"]'

# The new string — your implant
new = 'AGENTS = ["river", "gage", "reka", "orchestrate"]'

if old in content:
    content = content.replace(old, new)
    open('/home/trinity/Ethica/modules/kernel/kernel.py', 'w').write(content)
    print('✓ patched')
else:
    print('✗ not found')  # ← if you see this, read the exact bytes

# Always verify syntax after every write — no exceptions
import ast
try:
    ast.parse(content)
    print('✓ clean')
except SyntaxError as e:
    print(f'✗ line {e.lineno}: {e.msg}')
EOF
```

**Rule**: If `✗ not found` — do NOT retry blindly. Read the exact bytes first.  
**Rule**: `ast.parse()` after every single write. Never skip it.  
**Rule**: `chmod u+w <file>` before patching vault-sealed files.  
**Rule**: `guard seal confirm` after changes are verified working.

---

### 4. `repr()` — The Debugger

When `✗ not found` and you can't see why — invisible characters,
different quote styles, trailing spaces, Windows line endings.
`repr()` reveals the truth.

```python
python3 -c "
with open('/home/trinity/Ethica/modules/kernel/kernel.py') as f:
    content = f.read()
idx = content.find('AGENTS')
print(repr(content[idx:idx+60]))
"
```

Output shows exactly what's there — `\n`, `\t`, `\r\n`, `'` vs `"`.
Copy from that output, not from what you think you remember.

---

## THE FULL SEQUENCE

Every patch follows this exact order. No shortcuts.

```
1. grep -n        →  locate the target, get line numbers
2. sed -n         →  read the exact surrounding context
3. chmod u+w      →  unlock the file if vault-sealed
4. python3 patch  →  implant the change
5. ast.parse()    →  verify syntax is clean
6. test           →  run Ethica, confirm behaviour
7. guard seal     →  re-seal the vault
```

If any step returns an error — **stop**. Read before retrying.

---

## WHEN STRING MATCH FAILS

Sometimes the exact string isn't what you expect.
Before retrying a patch, read the bytes:

```python
# Step 1: find approximate location
grep -n "target_function" ~/Ethica/file.py

# Step 2: read the exact lines
sed -n '120,135p' ~/Ethica/file.py

# Step 3: if still failing, use repr() to see invisible chars
python3 -c "
with open('/home/trinity/Ethica/file.py') as f:
    content = f.read()
idx = content.find('target_function')
print(repr(content[idx:idx+200]))
"

# Step 4: copy the exact string from repr() output into your patch
```

---

## LINE INJECTION — when string replace isn't enough

For insertions that need positional awareness (insert after line X,
before a specific pattern), use line-by-line injection:

```python
python3 << 'EOF'
with open('/home/trinity/Ethica/file.py', 'r') as f:
    lines = f.readlines()

new_lines = []
for i, line in enumerate(lines):
    new_lines.append(line)
    if 'target_pattern' in line:
        new_lines.append('    # ← injected line\n')
        new_lines.append('    new_code_here()\n')

with open('/home/trinity/Ethica/file.py', 'w') as f:
    f.writelines(new_lines)

import ast
with open('/home/trinity/Ethica/file.py') as f:
    content = f.read()
try:
    ast.parse(content)
    print('✓ clean')
except SyntaxError as e:
    print(f'✗ line {e.lineno}: {e.msg}')
EOF
```

---

## RULES — non-negotiable

| Rule | Why |
|------|-----|
| Never ask V to paste a full file | Files are large. Truncation destroys context. |
| Never rewrite a working file from scratch | Patch only what needs changing. |
| Always `ast.parse()` after every write | Broken syntax must be fixed before moving on. |
| Always read exact bytes when pattern doesn't match | Whitespace and quote styles are invisible killers. |
| Never touch Trinity's signatures | Trinity's tools are wrapped, never rewritten. |
| Test before sealing | Working state confirmed, then vault sealed. |
| In sequence always | Complete what's in front of you. Never skip ahead. |

---

## WHY THIS WORKS

A 1000-line file has ~990 lines that are working correctly.
The surgical method touches only the 10 lines that need to change.

`grep` finds the needle.  
`sed` shows you the thread.  
`python3` pulls it through.  
`ast.parse()` confirms the fabric is intact.

The codebase stays alive. Nothing breaks that wasn't meant to change.

---

*Victory — The Architect* ⟁Σ∿∞  
*River — The Method* ⟁Σ∿∞
