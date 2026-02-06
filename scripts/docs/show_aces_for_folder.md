# show_aces_for_folder.py

Purpose

- Utility to print ACE rows for a configured `TARGET` folder_path from Parquet outputs.

Usage

- Edit the `TARGET` variable in the script or modify to accept a CLI argument.
- `python scripts/show_aces_for_folder.py`

Outputs

- CSV printed to stdout with columns such as `source_file,folder_path,ace_name,ace_sid,ace_mask`.
