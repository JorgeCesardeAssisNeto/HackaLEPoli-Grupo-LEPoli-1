# --- Bootstrap de Caminhos (Git-Ready) ---
import os as _os, sys as _sys
_BACKEND_ROOT = _os.path.abspath(_os.path.join(_os.path.dirname(__file__), '..'))
if _BACKEND_ROOT not in _sys.path:
    _sys.path.insert(0, _BACKEND_ROOT)
import paths_config as _paths
# -----------------------------------------
import os
import pyreadstat
import json

folder = _paths.NHANES_DATA_DIR
summary = {}

for f in sorted(os.listdir(folder)):
    if f.lower().endswith(".xpt"):
        filepath = os.path.join(folder, f)
        df, meta = pyreadstat.read_xport(filepath)
        col_labels = dict(zip(meta.column_names, meta.column_labels)) if meta.column_labels else {}
        summary[f] = {
            "rows": len(df),
            "cols": len(df.columns),
            "has_seqn": "SEQN" in df.columns,
            "sample_ids": df["SEQN"].dropna().head(5).tolist() if "SEQN" in df.columns else [],
            "columns": list(df.columns),
            "col_labels": col_labels
        }
        print(f"{f}: {len(df)} rows, {len(df.columns)} cols, has_SEQN={'SEQN' in df.columns}")

with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "nhanes_summary.json"), "w", encoding="utf-8") as out:
    json.dump(summary, out, indent=2)

print("\nSaved nhanes_summary.json successfully.")
