from pathlib import Path
import pandas as pd
import json

PARQUET_DIR = Path('out/parquet/run-20260202-124902')
OUT_CSV = Path('out/analysis/everyone_full_control.csv')

IDENTITY_PATTERNS = ['everyone', 's-1-1-0']

def is_everyone_name(name: str) -> bool:
    if not name:
        return False
    nl = name.lower()
    for p in IDENTITY_PATTERNS:
        if p in nl:
            return True
    return False

def is_full_control(mask) -> bool:
    if mask is None:
        return False
    if isinstance(mask, (int, float)):
        return int(mask) > 0
    s = str(mask).lower()
    return 'full' in s or 'fullcontrol' in s or 'full control' in s

def resolve_name(row):
    n = row.get('ace_name')
    if n and str(n).strip():
        return str(n).strip()
    raw = row.get('ace_raw')
    if not raw:
        return ''
    try:
        obj = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(obj, dict):
            for key in ('name','displayName','identity','account','accountName','sid'):
                v = obj.get(key) or obj.get(key.lower())
                if v:
                    return str(v).strip()
    except Exception:
        return str(raw).strip()
    return ''

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
        df.columns = [c.lower() for c in df.columns]
        dfs.append(df)

    if not dfs:
        print('No readable parquet content')
        return

    df = pd.concat(dfs, ignore_index=True)
    for col in ('ace_name','folder_path','ace_mask','ace_sid'):
        if col not in df.columns:
            df[col] = None

    df['res_name'] = df.apply(resolve_name, axis=1)

    out_rows = []
    for _, r in df.iterrows():
        raw_folder = r.get('folder_path')
        if pd.isna(raw_folder):
            continue
        folder = str(raw_folder).strip()
        if not folder or folder.lower() == 'nan':
            continue

        name = r.get('res_name') or ''
        mask = r.get('ace_mask')
        if is_everyone_name(name) and is_full_control(mask):
            out_rows.append({
                'folder_path': folder,
                'ace_name': name,
                'ace_mask': mask,
                'ace_sid': r.get('ace_sid'),
            })

    out = pd.DataFrame(out_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f'Found {len(out_rows)} ACEs where Everyone has FullControl. Results written to {OUT_CSV}')

if __name__ == '__main__':
    main()
