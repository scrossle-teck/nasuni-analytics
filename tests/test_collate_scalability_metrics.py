import csv
import json
import importlib.util
from pathlib import Path


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location("collate", str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def test_basic_counts(tmp_path: Path):
    run_dir = tmp_path / "run-1"
    folderacls = run_dir / "folderacls"
    folderacls.mkdir(parents=True)

    # create a JSON file with two entries: one valid, one with empty Path
    entries = [
        {"Path": "\\\\filer.example.com\\shareA\\folder1", "Access": [{}, {}]},
        {"Path": "", "Access": [{}, {}]},
    ]
    (folderacls / "sample.json").write_text(json.dumps(entries), encoding="utf-8")

    # create shares.csv to map shareA to a volume
    shares_file = run_dir / "shares.csv"
    with shares_file.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["filer_name", "share_name", "volume_name", "volume_guid"]) 
        w.writerow(["filer", "sharea", "volA", "guid-volA"])

    mod = load_module(Path("scripts/collate_scalability_metrics.py"))
    files_count, acl_entries, total_aces, aces_per_entry, per_host, per_volume = mod.process_run(run_dir)

    assert files_count == 1
    # one valid entry (the empty Path is ignored)
    assert acl_entries == 1
    assert total_aces == 2
    # per_host should have the filer short name
    assert "filer" in per_host
    # per_volume should have at least one entry with one acl entry
    assert len(per_volume) >= 1
    assert any(stats.get("acl_entries", 0) == 1 for stats in per_volume.values())


def test_unknown_volume(tmp_path: Path):
    run_dir = tmp_path / "run-2"
    folderacls = run_dir / "folderacls"
    folderacls.mkdir(parents=True)

    entries = [{"Path": "\\\\otherfiler.domain\\shareX\\f", "Access": [{}]}]
    (folderacls / "one.json").write_text(json.dumps(entries), encoding="utf-8")

    # no shares.csv -> should map to unknown
    mod = load_module(Path("scripts/collate_scalability_metrics.py"))
    files_count, acl_entries, total_aces, aces_per_entry, per_host, per_volume = mod.process_run(run_dir)

    assert files_count == 1
    assert acl_entries == 1
    assert total_aces == 1
    assert "unknown" in per_volume
