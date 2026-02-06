"""Analyze existing CSV `out/broad-perms.csv` to surface top identities and
folders with multiple broad ACEs.

Reads `out/broad-perms.csv` and prints ranked summaries to stdout.
Usage: `python scripts/analysis_broad_perms.py`
"""

import csv
from collections import defaultdict
from pathlib import Path
p = Path('out/broad-perms.csv')
if not p.exists():
    print('NO_FILE')
    raise SystemExit(1)

occ = defaultdict(int)
folders = defaultdict(set)
matched = defaultdict(set)
folder_aces = defaultdict(set)

with p.open(newline='', encoding='utf-8') as fh:
    r = csv.DictReader(fh)
    for row in r:
        name = (row.get('ace_name') or '').strip()
        folder = (row.get('folder_path') or '').strip()
        mr = (row.get('matched_rules') or '').strip()
        occ[name] += 1
        if folder:
            folders[name].add(folder)
            folder_aces[folder].add(name)
        if mr:
            for m in mr.split(','):
                matched[name].add(m.strip())


print('Top identities by distinct folder_count and occurrences:')
print(f"{'rank':>4} {'folder_count':>12} {'occurrences':>12} identity")
items = [(name, len(folders[name]), occ[name], ','.join(sorted(matched[name]))) for name in occ]
items.sort(key=lambda x: ( -x[1], -x[2], x[0].lower() ))
for i, (name, fc, oc, mr) in enumerate(items[:20], start=1):
    print(f"{i:4d} {fc:12d} {oc:12d} {name} {('('+mr+')') if mr else ''}")

print('\nFolders with multiple distinct broad-group ACEs:')
print(f"{'rank':>4} {'broad_ace_count':>16} folder_path")
folders_list = [(fld, len(aces)) for fld, aces in folder_aces.items()]
folders_list = [x for x in folders_list if x[1] > 1]
folders_list.sort(key=lambda x: (-x[1], x[0]))
for i, (fld, c) in enumerate(folders_list[:50], start=1):
    print(f"{i:4d} {c:16d} {fld}")
