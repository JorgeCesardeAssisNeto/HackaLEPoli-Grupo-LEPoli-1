# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
with open(_os.path.join(_paths.CORE_API_DIR, 'templates', 'index.html'), 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div[^>]*id="(view-[^"]+)"[^>]*class="([^"]+)"', text)
for m in matches:
    print(m[0], "-->", m[1])
