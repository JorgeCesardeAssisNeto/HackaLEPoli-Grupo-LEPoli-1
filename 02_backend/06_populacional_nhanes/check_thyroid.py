# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import urllib.request
import re

url = "https://wwwn.cdc.gov/nchs/nhanes/continuousnhanes/default.aspx?Cycle=2017-2020"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
try:
    with urllib.request.urlopen(req) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
        matches = [m for m in re.findall(r'href=[\'"]([^\'"]+)[\'"]', html) if "thyr" in m.lower()]
        print("Thyroid links in 2017-2020:", matches)
        all_xpt = [m for m in re.findall(r'href=[\'"]([^\'"]+\.XPT)[\'"]', html, re.I)]
        print("XPT files count:", len(all_xpt))
        for x in all_xpt:
            if any(k in x.lower() for k in ["thyr", "tsh", "t4"]):
                print("Found match:", x)
except Exception as e:
    print("Error:", e)
