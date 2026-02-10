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
           make_row(r'\\\\filer\\shareA\\f', 'RegularUser', 'S-1-5-21-100', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'NonAdminFullControl' for m in matches)


def test_orphaned_sid_fullcontrol_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\filer\\shareB\\g', '', 'S-1-5-9999', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'OrphanedSIDsFullControl' for m in matches)


def test_sensitive_folder_write_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\filer\\share\\Finance\\reports', 'Alice', 'S-1-5-21-200', 'Modify'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'SensitiveFoldersWrite' for m in matches)


def test_acl_too_many_aces_matches():
    rules = load_rules()
    rows = [make_row(r'\\f\\share\\big', f'User{i}', f'S-1-5-21-{i}', 'Read') for i in range(150)]
    df = pd.DataFrame(rows)
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'AclTooManyAces' for m in matches)


def test_duplicate_ace_entries_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\s\\dup', 'Bob', 'S-1-5-21-300', 'Read'),
           make_row(r'\\\\f\\s\\dup', 'Bob', 'S-1-5-21-300', 'Read'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'DuplicateAceEntries' for m in matches)


def test_service_account_fullcontrol_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\svc\\data', 'backup_svc', 'S-1-5-21-500', 'FullControl'),
           make_row(r'\\\\f\\svc\\data', 'serviceAccount$', 'S-1-5-21-501', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'ServiceAccountFullControl' for m in matches)


def test_auth_users_broad_perms_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\share\\pub', 'Authenticated Users', 'S-1-5-11', 'Modify'),
           make_row(r'\\\\f\\share\\pub', 'ANONYMOUS LOGON', 'S-1-5-7', 'Write'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'AuthUsersBroadPerms' for m in matches)


def test_takeownership_or_changeperms_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\share\\secure', 'Alice', 'S-1-5-21-600', 'WRITE_OWNER'),
           make_row(r'\\\\f\\share\\secure', 'Bob', 'S-1-5-21-601', 'Write_DAC'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'TakeOwnershipOrChangePerms' for m in matches)


def test_external_principal_access_matches():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\ext\\docs', 'user@example.com', 'S-1-5-21-700', 'Read'),
    ])
    matches = apply_rules_df(df, rules)
    assert any(m['rule_id'] == 'ExternalPrincipalAccess' for m in matches)


def test_admin_not_flagged_as_nonadmin_fullcontrol():
    rules = load_rules()
    df = pd.DataFrame([
           make_row(r'\\\\f\\admin\\root', 'Administrators', 'S-1-5-32-544', 'FullControl'),
    ])
    matches = apply_rules_df(df, rules)
    # should not flag NonAdminFullControl for known admin identities
    assert not any(m['rule_id'] == 'NonAdminFullControl' for m in matches)
