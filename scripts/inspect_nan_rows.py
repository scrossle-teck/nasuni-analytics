from pathlib import Path
import pandas as pd
import json
import sys

PARQUET_DIR = Path('out/parquet/run-20260202-124902')
OUT_CSV = Path('out/analysis/nan_rows_debug.csv')

def main():
    files = sorted(PARQUET_DIR.glob('*.parquet'))
    if not files:
        print('No parquet files found in', PARQUET_DIR)
        return

    dfs = []
    for f in files:
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        # normalize column names to lowercase
        df.columns = [c.lower() for c in df.columns]
        df['source_file'] = str(f)
        dfs.append(df)

    if not dfs:
        print('No readable parquet content')
        return

    df = pd.concat(dfs, ignore_index=True)

    # ensure folder_path column exists
    if 'folder_path' not in df.columns:
        df['folder_path'] = None

    # find rows where folder_path is missing, NaN, empty or the string 'nan'
    bad_mask = df['folder_path'].isna() | df['folder_path'].astype(str).str.lower().isin(['nan', ''])
    bad = df[bad_mask].copy()

    print('Problematic rows found:', len(bad))
    if bad.empty:
        return

    # select useful debug columns if present
    cols = []
    for c in ('source_file','folder_path','ace_raw','ace_name','ace_sid','ace_mask','ace_inherited'):
        if c in bad.columns:
            cols.append(c)
    if not cols:
        cols = ['source_file','folder_path']

    # write CSV for inspection and print sample
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    bad.to_csv(OUT_CSV, columns=cols, index=False)
    print('Wrote debug CSV to', OUT_CSV)
    # print up to 50 sample rows
    pd.set_option('display.max_colwidth', 200)
    print(bad[cols].head(50).to_string(index=False))

if __name__ == '__main__':
    main()
