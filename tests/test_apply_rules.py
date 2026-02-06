import pandas as pd
from pathlib import Path
import sys

# allow importing scripts package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.apply_rules import load_rules, apply_rules_df


def make_row(folder, name, sid, mask, inh=False, raw=None):
    return {
        'folder_path': folder,
        'ace_name': name,
        'ace_sid': sid,
        'ace_mask': mask,
        'ace_inherited': inh,
        'ace_raw': raw,
    }


def test_non_admin_fullcontrol_matches():
    rules = load_rules()
    df = pd.DataFrame([
        make_row('\\\\filer\\shareA\\f', 'RegularUser', 'S-1-5-21-100', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'NonAdminFullControl' for m in matches)


def test_orphaned_sid_fullcontrol_matches():
    rules = load_rules()
    df = pd.DataFrame([
        make_row('\\\\filer\\shareB\\g', '', 'S-1-5-9999', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'OrphanedSIDsFullControl' for m in matches)


def test_sensitive_folder_write_matches():
    rules = load_rules()
    df = pd.DataFrame([
        make_row('\\\\filer\\share\\Finance\\reports', 'Alice', 'S-1-5-21-200', 'Modify'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'SensitiveFoldersWrite' for m in matches)


def test_acl_too_many_aces_matches():
    rules = load_rules()
    rows = [make_row('\\\\f\\share\\big', f'User{i}', f'S-1-5-21-{i}', 'Read') for i in range(150)]
    df = pd.DataFrame(rows)
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'AclTooManyAces' for m in matches)


def test_duplicate_ace_entries_matches():
    rules = load_rules()
    df = pd.DataFrame([
        make_row('\\\\f\\s\\dup', 'Bob', 'S-1-5-21-300', 'Read'),
        make_row('\\\\f\\s\\dup', 'Bob', 'S-1-5-21-300', 'Read'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'DuplicateAceEntries' for m in matches)
