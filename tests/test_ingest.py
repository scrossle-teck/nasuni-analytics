import json
import sys
from pathlib import Path

import pandas as pd

# Ensure repo root is on sys.path so `scripts` is importable from tests
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.ingest_duckdb import process_run


def make_sample_run(tmp_path: Path) -> Path:
    run_dir = tmp_path / "runs" / "run-test-1"
    folderacls = run_dir / "folderacls"
    folderacls.mkdir(parents=True, exist_ok=True)
    # Use new schema (1.0.1): UncPath and Access with Identity/Rights/IsInherited
    sample = [
        {
            "UncPath": "\\\\nasuni\\share\\folder1",
            "CollectedUtc": "2026-02-09T12:00:00Z",
            "CollectionHost": "host.example",
            "Collector": "collector",
            "Owner": "owner",
            "Sddl": "S:...",
            "Access": [
                {"Identity": "Domain Users", "Rights": "FullControl", "Type": "allow", "IsInherited": False},
                {"Identity": "Admins", "Rights": "Read", "Type": "allow", "IsInherited": False}
            ],
            "FingerprintSha256": "abc",
            "CollectionSha256": "def"
        }
    ]

    sample_file = folderacls / "sample.json"
    with open(sample_file, "w", encoding="utf-8") as fh:
        json.dump(sample, fh)

    return run_dir


def test_process_run_writes_parquet(tmp_path: Path):
    run_dir = make_sample_run(tmp_path)
    out_dir = tmp_path / "out"
    # run ingestion
    process_run(str(run_dir), str(out_dir))

    run_id = run_dir.name
    target = out_dir / run_id
    # expect one parquet file
    files = list(target.glob("*.parquet"))
    assert len(files) == 1

    df = pd.read_parquet(files[0])
    # expected columns from the ingestion script
    expected_cols = {"source_file", "folder_path", "ace_sid", "ace_name", "ace_type", "ace_mask", "ace_inherited", "ace_raw"}
    assert expected_cols.issubset(set(df.columns))

    # check that Domain Users row exists
    names = set(df['ace_name'].dropna().astype(str).tolist())
    assert any('Domain Users' in n for n in names)
