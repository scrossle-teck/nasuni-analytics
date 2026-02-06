import pandas as pd
from pathlib import Path
import sys

# allow importing scripts package
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.apply_rules import apply_rules_df


def make_row(folder, name, sid, mask, inh=False, raw=None):
    return {
        'folder_path': folder,
        'ace_name': name,
        'ace_sid': sid,
        'ace_mask': mask,
        'ace_inherited': inh,
        'ace_raw': raw,
    }


def test_min_severity_filters_out_lower_severity():
    rules = [
        {'id': 'r_low', 'identity_patterns': ['alice'], 'severity': 'low'},
        {'id': 'r_med', 'identity_patterns': ['eve'], 'severity': 'medium'},
        {'id': 'r_high', 'identity_patterns': ['bob'], 'severity': 'high'},
    ]

    rows = [
        make_row('\\f\s\a', 'alice', 'S-1-5-21-1', 'Read'),
        make_row('\\f\s\b', 'bob', 'S-1-5-21-2', 'Read'),
        make_row('\\f\s\e', 'eve', 'S-1-5-21-3', 'Read'),
    ]
    df = pd.DataFrame(rows)

    # min_severity medium: should include medium+high (eve, bob) but not low (alice)
    matches = apply_rules_df(df, rules, min_severity='medium')
    ids = {m['rule_id'] for m in matches}
    assert 'r_low' not in ids
    assert 'r_med' in ids
    assert 'r_high' in ids


def test_min_severity_low_all_included():
    rules = [
        {'id': 'r_low', 'identity_patterns': ['alice'], 'severity': 'low'},
        {'id': 'r_high', 'identity_patterns': ['bob'], 'severity': 'high'},
    ]
    rows = [make_row('\\f\s\a', 'alice', 'S-1-5-21-1', 'Read'), make_row('\\f\s\b', 'bob', 'S-1-5-21-2', 'Read')]
    df = pd.DataFrame(rows)
    matches = apply_rules_df(df, rules, min_severity='low')
    ids = {m['rule_id'] for m in matches}
    assert 'r_low' in ids and 'r_high' in ids
