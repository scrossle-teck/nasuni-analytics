from pathlib import Path
import pandas as pd
import json

PARQUET_DIR = Path('out/parquet/run-20260202-124902')
OUT_CSV = Path('out/analysis/sensitive_shares_broad_perms.csv')

# keyword groups: canonical -> list of patterns (lowercase)
KEYWORDS = {
    'HR': ['hr', 'human resources', 'recursos humanos', 'rrhh'],
    'Payroll': ['payroll', 'nomina', 'nómina', 'salary', 'sueldo', 'salario'],
    'Finance': ['finance', 'finanzas', 'accounting', 'contabilidad', 'tax', 'taxes', 'impuestos'],
    'Legal': ['legal', 'contracts', 'contratos', 'contract', 'contrato'],
    'Confidential': ['confidential', 'confidencial', 'sensitive', 'privado', 'private'],
    'PII': ['pii', 'personal data', 'personal', 'personnel', 'identification', 'identificacion'],
    'Security': ['security', 'seguridad', 'itgc', 'sox'],
    'Health': ['health', 'salud', 'medical', 'medico', 'medicina'],
}

# identities considered 'broad' (common names/SIDs/keywords)
BROAD_IDENTITIES = ['everyone', 's-1-1-0', 'authenticated', 'domain users', 'g-r-all', 'all-nasuni', 'all-nasuni-everyone']

# admin identity patterns to exclude from sensitive hits
ADMIN_PATTERNS = [
    'admin', 'g-f-all-full-control', 'g-r-admin', 'g-r-all', 'nasuni-administrator',
    'administrator', 'system', 's-1-22-1-0', 's-1-5-18', 'nt authority\\system'
]

def is_admin_name(name: str) -> bool:
    if not name:
        return False
    nl = name.lower()
    for p in ADMIN_PATTERNS:
        if p in nl:
            return True
    return False

def is_broad_identity(name: str) -> bool:
    if not name:
        return False
    nl = name.lower()
    for p in BROAD_IDENTITIES:
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

def match_keyword(path_lower: str):
    for canon, patterns in KEYWORDS.items():
        for p in patterns:
            if p in path_lower:
                return canon, p
    return None, None

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
    for col in ('ace_name','folder_path','ace_mask','ace_sid','ace_inherited'):
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

        folder_l = folder.lower()
        canon, matched = match_keyword(folder_l)
        if not canon:
            continue

        name = r.get('res_name') or ''
        mask = r.get('ace_mask')
        # skip ACEs that are from admin/service groups we already expect
        if is_admin_name(name):
            continue
        if is_broad_identity(name) and is_full_control(mask):
            out_rows.append({
                'folder_path': folder,
                'keyword_group': canon,
                'matched_pattern': matched,
                'ace_name': name,
                'ace_mask': mask,
                'ace_sid': r.get('ace_sid'),
                'ace_inherited': r.get('ace_inherited'),
            })

    out = pd.DataFrame(out_rows)
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(OUT_CSV, index=False)
    print(f'Found {len(out_rows)} matching ACEs. Results written to {OUT_CSV}')

if __name__ == '__main__':
    main()
