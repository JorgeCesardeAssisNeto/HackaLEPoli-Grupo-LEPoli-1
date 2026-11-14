# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import sys

with open(_os.path.join(_paths.GERADORES_DIR, 'test_script.js'), encoding='utf-8') as f:
    lines = f.readlines()

depth = 0
in_template = False
in_str_single = False
in_str_double = False
in_comment_line = False
in_comment_block = False

for line_no, line in enumerate(lines, 1):
    i = 0
    while i < len(line):
        ch = line[i]
        nxt = line[i+1] if i+1 < len(line) else ''
        
        if in_comment_line:
            break
        elif in_comment_block:
            if ch == '*' and nxt == '/':
                in_comment_block = False
                i += 1
        elif in_template:
            if ch == '`':
                in_template = False
            elif ch == '$' and nxt == '{':
                depth += 1
                i += 1
        elif in_str_single:
            if ch == '\\':
                i += 1
            elif ch == "'":
                in_str_single = False
        elif in_str_double:
            if ch == '\\':
                i += 1
            elif ch == '"':
                in_str_double = False
        else:
            if ch == '/' and nxt == '/':
                break
            elif ch == '/' and nxt == '*':
                in_comment_block = True
                i += 1
            elif ch == '`':
                in_template = True
            elif ch == "'":
                in_str_single = True
            elif ch == '"':
                in_str_double = True
            elif ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth < 0:
                    print(f"ERRO: Chave extra fechando na linha {line_no}: {line.strip()[:80]}")
                    depth = 0
        i += 1

print(f"Final depth: {depth}")
