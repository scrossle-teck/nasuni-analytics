import csv
import os

inpath = os.path.join('out','rule_matches.csv')
outs = {
    'low': os.path.join('out','rule_matches_low.csv'),
    'medium': os.path.join('out','rule_matches_medium.csv'),
    'high': os.path.join('out','rule_matches_high.csv'),
}

with open(inpath, newline='', encoding='utf-8') as inf:
    rdr = csv.DictReader(inf)
    # DictReader.fieldnames may be None; coerce to a list for DictWriter
    fieldnames = list(rdr.fieldnames or [])
    writers = {}
    files = {}
    for sev, path in outs.items():
        f = open(path, 'w', newline='', encoding='utf-8')
        files[sev] = f
        writers[sev] = csv.DictWriter(f, fieldnames=fieldnames)
        if fieldnames:
            writers[sev].writeheader()

    for row in rdr:
        sev = (row.get('severity') or '').lower()
        if sev in writers:
            writers[sev].writerow(row)

    for f in files.values():
        f.close()

print('Wrote severity-split files to out/')
