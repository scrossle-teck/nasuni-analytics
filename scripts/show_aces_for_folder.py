"""Utility to show ACEs for a specific `folder_path` from Parquet outputs.

Edit `TARGET` in the script or modify to accept a CLI arg. Prints CSV to stdout.
Usage: `python scripts/show_aces_for_folder.py`
"""

from pathlib import Path
import pandas as pd

PARQUET_DIR = Path('out/parquet/run-20260202-124902')
TARGET = r"\\trlfilp101.teckcominco.loc\az-centralus-trl01-nasuni"

def main():
    files = sorted(PARQUET_DIR.glob('*.parquet'))
    if not files:
        print('No parquet files found in', PARQUET_DIR)
        return

    rows = []
    for f in files:
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        df.columns = [c.lower() for c in df.columns]
        if 'folder_path' not in df.columns:
            continue
        sel = df[df['folder_path'].astype(str).str.strip() == TARGET]
        if not sel.empty:
            rows.append(sel)

    if not rows:
        print('No ACE rows found for', TARGET)
        return

    out = pd.concat(rows, ignore_index=True)
    cols = [c for c in ('source_file','folder_path','ace_name','ace_sid','ace_mask','ace_inherited','matched_rules','ace_raw') if c in out.columns]
    print(out[cols].to_csv(index=False))

if __name__ == '__main__':
    main()
