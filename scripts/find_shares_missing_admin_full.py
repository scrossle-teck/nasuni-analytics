from pathlib import Path
import pandas as pd
import json

PARQUET_DIR = Path('out/parquet/run-20260202-124902')
OUT_CSV = Path('out/analysis/shares_missing_admin_full.csv')

ADMIN_PATTERNS = ['admin', 'g-f-all-full-control', 's-1-22-1-0', 'system', 's-1-5-18', 'nt authority\\system']

def is_admin_name(name: str) -> bool:
    if not name:
        return False
    nl = name.lower()
    for p in ADMIN_PATTERNS:
        if p in nl:
            return True
    return False

def is_full_control(mask) -> bool:
    if mask is None:
        return False
    if isinstance(mask, (int, float)):
        # conservative: treat large masks as potentially full; caller can refine
        return int(mask) > 0
    s = str(mask).lower()
    return 'full' in s or 'fullcontrol' in s or 'full control' in s

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
    for col in ('ace_name','folder_path','ace_mask'):
        if col not in df.columns:
            df[col] = None

    # normalize ace_name via ace_raw if missing
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

    df['res_name'] = df.apply(resolve_name, axis=1)

    grouped = {}
    for _, r in df.iterrows():
        raw_folder = r.get('folder_path')
        if pd.isna(raw_folder):
            continue
        folder = str(raw_folder).strip()
        if not folder:
            continue
        if folder.lower() == 'nan':
            continue
        grouped.setdefault(folder, []).append(r)

    missing = []
    for folder, rows in grouped.items():
        has_admin_full = False
        for r in rows:
            name = r.get('res_name') or ''
            mask = r.get('ace_mask')
            if is_admin_name(name) and is_full_control(mask):
                has_admin_full = True
                break
        if not has_admin_full:
            missing.append({'folder_path': folder, 'ace_count': len(rows)})

    out = pd.DataFrame(missing)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f'Found {len(missing)} folders without an admin group with FullControl. Results written to {OUT_CSV}')

if __name__ == '__main__':
    main()
