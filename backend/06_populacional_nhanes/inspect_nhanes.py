import os
import pyreadstat
import json

folder = "Dados NHANHES"
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

with open("nhanes_summary.json", "w", encoding="utf-8") as out:
    json.dump(summary, out, indent=2)

print("\nSaved nhanes_summary.json successfully.")
