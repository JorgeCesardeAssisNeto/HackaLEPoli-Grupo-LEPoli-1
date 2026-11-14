# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
with open(_os.path.join(_paths.CORE_API_DIR, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
    text = f.read()

script_start = text.find('<script>') + 8
script_end = text.rfind('</script>')
js = text[script_start:script_end]

# Simple JS lexer for braces and parens
stack = []
i = 0
n = len(js)
line_no = text[:script_start].count('\n') + 1

while i < n:
    c = js[i]
    if c == '\n':
        line_no += 1
        i += 1
        continue
    # skip single line comment
    if c == '/' and i + 1 < n and js[i+1] == '/':
        while i < n and js[i] != '\n':
            i += 1
        continue
    # skip multi line comment
    if c == '/' and i + 1 < n and js[i+1] == '*':
        i += 2
        while i < n - 1 and not (js[i] == '*' and js[i+1] == '/'):
            if js[i] == '\n':
                line_no += 1
            i += 1
        i += 2
        continue
    # skip single quote string
    if c == "'":
        i += 1
        while i < n and js[i] != "'":
            if js[i] == '\\':
                i += 1
            elif js[i] == '\n':
                line_no += 1
            i += 1
        i += 1
        continue
    # skip double quote string
    if c == '"':
        i += 1
        while i < n and js[i] != '"':
            if js[i] == '\\':
                i += 1
            elif js[i] == '\n':
                line_no += 1
            i += 1
        i += 1
        continue
    # skip template literal
    if c == '`':
        i += 1
        while i < n and js[i] != '`':
            if js[i] == '\\':
                i += 1
            elif js[i] == '\n':
                line_no += 1
            i += 1
        i += 1
        continue

    # brackets and parens
    if c in '({[':
        stack.append((c, line_no, i))
    elif c in ')}]':
        if not stack:
            print(f"Unexpected closing {c} at line {line_no}")
        else:
            top_char, top_line, _ = stack.pop()
            expected = {'(': ')', '{': '}', '[': ']'}[top_char]
            if c != expected:
                print(f"Mismatched bracket at line {line_no}: got {c}, expected {expected} from line {top_line}")
    i += 1

if stack:
    print(f"Unclosed items ({len(stack)}):")
    for item in stack[-5:]:
        print(f"  Unclosed {item[0]} from line {item[1]}")
else:
    print("ALL PARENS, BRACES AND BRACKETS MATCH PERFECTLY!")
