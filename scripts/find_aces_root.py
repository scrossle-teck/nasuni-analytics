from pathlib import Path
import pandas as pd
import json

PARQUET_DIR = Path('out/parquet/run-20260202-124902')

def resolve_name_from_raw(raw):
    if not raw:
        return ''
    try:
        obj = json.loads(raw) if isinstance(raw, str) else raw
        if isinstance(obj, dict):
            for key in ('name','displayName','identity','account','accountName','sid'):
                v = obj.get(key) or obj.get(key.lower())
                if v:
                    return str(v)
    except Exception:
        return str(raw)
    return str(raw)

def main():
    files = sorted(PARQUET_DIR.glob('*.parquet'))
    if not files:
        print('No parquet files found in', PARQUET_DIR)
        return

    matches = {}
    for f in files:
        try:
            df = pd.read_parquet(f)
        except Exception:
            continue
        df.columns = [c.lower() for c in df.columns]
        if 'ace_name' in df.columns:
            for v in df['ace_name'].dropna().astype(str):
                if 'root' in v.lower():
                    matches[v] = matches.get(v, 0) + 1
        # also inspect ace_raw
        if 'ace_raw' in df.columns:
            for raw in df['ace_raw'].dropna().astype(str):
                if 'root' in raw.lower():
                    name = resolve_name_from_raw(raw)
                    matches[name] = matches.get(name, 0) + 1

    if not matches:
        print('No ACE names or raw ACEs containing "root" found.')
        return

    items = sorted(matches.items(), key=lambda x: -x[1])
    print('Found ACE name matches containing "root":')
    for name, cnt in items:
        print(f'{cnt:6d}  {name}')

if __name__ == '__main__':
    main()
