from pathlib import Path
import json
import pandas as pd
from collections import defaultdict

pdir = Path('out/parquet/run-20260202-124902')
files = sorted(pdir.glob('*.parquet'))
if not files:
    print('No parquet files found in', pdir)
    raise SystemExit(1)

print('Found', len(files), 'parquet files')

# Read in batches to avoid memory spikes
rows = []
for f in files:
    try:
        df = pd.read_parquet(f)
    except Exception as e:
        print('Failed to read', f, e)
        continue
    # normalize column names to expected keys
    df.columns = [c.lower() for c in df.columns]
    rows.append(df)

if not rows:
    print('No readable parquet content')
    raise SystemExit(1)

df = pd.concat(rows, ignore_index=True)
# ensure expected columns exist
for col in ('ace_name','folder_path','matched_rules','ace_mask'):
    if col not in df.columns:
        df[col] = ''

# compute stats
folders = defaultdict(set)
matched = defaultdict(set)
folder_aces = defaultdict(set)
occ = defaultdict(int)

def resolve_name_from_raw(ace_raw):
    if not ace_raw:
        return ''
    if isinstance(ace_raw, str):
        try:
            obj = json.loads(ace_raw)
        except Exception:
            return ace_raw.strip()
    else:
        obj = ace_raw

    if isinstance(obj, dict):
        low = {k.lower(): v for k, v in obj.items()}
        for candidate in ('name','displayname','identity','identityreference','account','accountname','principal','user','group','grantee','sid'):
            v = low.get(candidate)
            if v:
                return str(v).strip()
    return str(obj).strip() if obj is not None else ''

for _, r in df.iterrows():
    raw_name = str(r.get('ace_name','') or '').strip()
    folder = str(r.get('folder_path','') or '').strip()
    mr = str(r.get('matched_rules','') or '').strip()
    ace_raw = r.get('ace_raw', '')

    name = raw_name
    if not name:
        name = resolve_name_from_raw(ace_raw)

    if name:
        folders[name].add(folder)
        occ[name] += 1
    else:
        occ[''] += 1

    if folder:
        folder_aces[folder].add(name)

    if mr:
        for m in [x.strip() for x in mr.split(',') if x.strip()]:
            matched[name].add(m)

items = [(name, len(folders.get(name,[])), occ.get(name,0), ','.join(sorted(matched.get(name,[])))) for name in occ]
items.sort(key=lambda x: (-x[1], -x[2], x[0].lower()))

print('\nTop identities by distinct folder_count and occurrences:')
print(f"{'rank':>4} {'folder_count':>12} {'occurrences':>12} identity")
for i, (name, fc, oc, mr) in enumerate(items[:20], start=1):
    print(f"{i:4d} {fc:12d} {oc:12d} {name} {('('+mr+')') if mr else ''}")

# folders with multiple distinct broad-group ACEs
folders_list = [(fld, len(aces)) for fld, aces in folder_aces.items()]
folders_list = [x for x in folders_list if x[1] > 1]
folders_list.sort(key=lambda x: (-x[1], x[0]))

print('\nFolders with multiple distinct broad-group ACEs:')
print(f"{'rank':>4} {'broad_ace_count':>16} folder_path")
for i, (fld, c) in enumerate(folders_list[:100], start=1):
    print(f"{i:4d} {c:16d} {fld}")
