# find_everyone_full_control.py

Purpose

- Extract ACE entries where `Everyone` (or equivalent SIDs) has FullControl.

Usage

- `python scripts/find_everyone_full_control.py`

Outputs

- `out/analysis/everyone_full_control.csv`

Notes

- Useful quick check for globally permissive ACLs.
