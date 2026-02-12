# Project Guidelines — ACL Inventory, Risk Analytics, and Effective Access (Nasuni + AD)

> Living document. Greenfield-oriented, but aligned with the current direction of `nasuni-inventory` (collection) and `nasuni-analytics` (Parquet/DuckDB analysis).
>
> Primary goals:
>
> 1. Detect and report overly broad permissions and other gaps at enterprise scale.
> 2. Provide a “simulated / view-as” capability for effective NTFS access for a given user (and, for admins, for someone else).
>
> Assumptions in scope for this document:
>
> - Source of truth for identity is **on‑prem Active Directory** (Microsoft shop).
> - We can collect and persist ACL snapshot evidence from file servers / Nasuni exports.
> - We want a dataset that other tools can build on long-term.

Implementation breakdown:

- See `docs/work-packages/README.md` for the multi-day work packages.
- See `docs/work-packages/addendums/README.md` for per-work-package addendums (what’s already built + steps to reach acceptance).

---

## 0) Glossary (shared language)

- **Object**: a thing we can apply permissions to (share root, folder path). In our context, primarily folders.
- **ACE**: access control entry (one line in an ACL) that grants/denies rights to a principal.
- **ACL**: list of ACEs for an object (including inheritance semantics).
- **Principal**: security entity (user/group/computer/service) represented by SID and/or directory identity.
- **Security context set**: for a user, the set of SIDs that should be evaluated for access checks (user SID + group SIDs + well-known SIDs as appropriate).
- **Broad access**: permissions granted to a principal with large membership / unclear scope (Everyone, Authenticated Users, Domain Users, large org groups, etc.).
- **Blast radius**: number of enabled users who receive a given right (read/write/etc.) via a principal (possibly through nested groups).
- **Snapshot**: a point-in-time capture of ACLs and identity state.
- **Delta**: changes between snapshots, ideally computed from fingerprints/keys rather than full rescans.

---

## 1) North Star (what “done” looks like)

### 1.1 Outcomes

- **Enterprise risk reporting**
  - Identify where broad principals have risky rights (write/modify/fullcontrol) on sensitive paths or generally.
  - Identify missing expected admin controls (e.g., lack of an admin principal with FullControl at share roots).
  - Identify drift: “what changed since last run?” with severity and attribution where possible.

- **Effective access simulation**
  - Given a user (or SID), answer questions like:
    - “Which share roots/folders does Alice have write access to?”
    - “Why?” (show the matched ACEs and group chain)
    - “What changed since last week that increased Alice’s access?”

### 1.2 Non-goals (initially)

Be explicit about what is _not_ modeled at MVP to avoid over-claiming:

- Share permissions combined with NTFS permissions (unless share perms are also ingested).
- Privilege-based bypass (Backup Operators, local admin on server, SeTakeOwnership, etc.).
- Claims-based auth / Dynamic Access Control.
- Real-time evaluation (initially we operate on snapshots).

---

## 2) Core principles (design constraints that keep us sane)

1. **Raw facts are immutable**

- Keep raw evidence in a durable format (Parquet is preferred in `nasuni-analytics`).
- Never mutate raw data; transform into derived tables.

2. **Prefer “catalog + joins” over “blobs everywhere”**

- Store objects and ACE rows in a tabular way.
- Keep `ace_raw` (fidelity) but query primarily off canonical columns.

3. **Separate objects from policies**

- An ACL definition is a reusable policy.
- Many folders share identical ACLs; we should deduplicate using fingerprints.

4. **Snapshots + deltas over periodic full scans**

- Most value comes from detecting _changes_ and _outliers_, not re-proving the entire estate weekly.

5. **Make identity a first-class dataset**

- AD is the truth: ingest it on a schedule and join to ACL evidence.

6. **Scalability via pushdown**

- Prefer DuckDB/SQL over loading all Parquet into pandas at once.

---

## 3) Architecture overview (two repos, one pipeline)

### 3.1 `nasuni-inventory` (collection)

Responsibilities:

- Collect and normalize raw evidence from Nasuni/file servers (appliances/volumes/shares/visitlist/folder ACLs).
- Validate outputs against schema.
- Produce a consistent, deterministic “run folder” that can be ingested.

Outputs:

- Run directory with:
  - appliances/volumes/shares/visitlist CSVs
  - folder ACL JSON files (or other raw evidence)
  - schema sidecar
  - a manifest or summary (counts/timing) if available

### 3.2 `nasuni-analytics` (ingest + analysis)

Responsibilities:

- Ingest collection outputs to Parquet.
- Canonicalize, dedupe, fingerprint ACLs.
- Ingest AD identity snapshots.
- Run rule-based and metric-based analytics.
- Provide effective-access query capability over snapshots.

Outputs:

- Parquet datasets under `out/parquet/...`
- Findings CSVs under `out/analysis/...`

---

## 4) Canonical data model (tables / files)

> This is the “contract” other tools should rely on. Favor stable names and minimal churn.

### 4.1 Filesystem evidence tables

**A) Objects** (one row per folder/object)

Recommended columns:

- `run_id` (string): which inventory snapshot this comes from
- `object_id` (string): stable identifier if available; otherwise derived (see below)
- `server` (string)
- `share` (string)
- `folder_path` (string): canonical path
- `depth` (int): optional, for hierarchy analysis
- `discovered_at` (timestamp): when this object was observed
- `source_file` (string): provenance for debugging

Notes:

- If you do not have a stable object id from the source, derive `object_id` from normalized `server + share + folder_path`.

**B) ACE rows** (one row per ACE)

Required canonical columns (already used widely):

- `folder_path`
- `ace_name`
- `ace_sid`
- `ace_mask` (numeric)
- `ace_inherited` (boolean)
- `ace_raw` (json/string)

Recommended additional columns for future-proofing:

- `ace_type` (allow/deny) if known
- `ace_flags` (inheritance flags)
- `ace_source` (where it came from)

**C) ACL fingerprinting**

- `acl_fingerprint` (string): hash of the canonicalized ACL representation.
- `acl_ace_count` (int)

Tables:

- `acl_definitions(acl_fingerprint, canonical_acl_json, acl_ace_count, canonicalization_version)`
- `object_acl(object_id, acl_fingerprint, is_protected, owner_sid, collected_at)`

Why this matters:

- Risk scoring runs over unique ACLs first.
- Diffs become trivial: `acl_fingerprint` changed ⇒ ACL changed.

### 4.2 Identity evidence tables (AD snapshot)

**A) Principals**

`principals` columns:

- `snapshot_id` (string)
- `sid` (string) — primary join key to ACEs
- `object_guid` (string)
- `samaccountname` (string)
- `distinguished_name` (string)
- `principal_type` (enum-ish: user/group/computer/service)
- `enabled` (bool)
- `collected_at` (timestamp)

**B) Membership edges**

`membership_edges` columns:

- `snapshot_id`
- `member_sid`
- `group_sid`

**C) Membership closure (transitive)**

`membership_closure` columns:

- `snapshot_id`
- `member_sid`
- `group_sid`

Notes:

- Computing closure is expensive but usually worth it.
- With closure precomputed, effective access queries become joins, not graph traversals.

---

## 5) Ingest pipeline (recommended steps)

### 5.1 Inventory ingest → Parquet

- Input: `runs/run-*/` from `nasuni-inventory`
- Output: `out/parquet/run-<run_id>/` with canonical columns
- Requirements:
  - All column names lowercased in Parquet
  - Preserve raw fidelity (`ace_raw`) and stable identifiers (SIDs, numeric masks)

### 5.2 Canonicalization and fingerprint computation

Canonicalization rules should be versioned (so fingerprints are explainable):

- Stable ordering of ACEs for fingerprinting (e.g., sort by `ace_sid`, `ace_type`, `ace_mask`, inheritance flags)
- Normalize null/empty values consistently
- Decide representation for `ace_name` (keep raw + best-effort display name)

Fingerprint definition:

- `acl_fingerprint = hash(canonical_acl_representation)`

Deliverables:

- `acl_definitions.parquet`
- `object_acl.parquet`

### 5.3 AD identity ingest

Two viable approaches (choose based on operational constraints):

1. **PowerShell AD module snapshot** (Windows-centric, easy in Microsoft shops)

- Pros: minimal custom LDAP code, uses built-in tooling
- Cons: may require RSAT/AD module presence and Windows runners

2. **Python LDAP ingestion** (cross-platform, explicit)

- Pros: portable, consistent with analytics tooling
- Cons: more code, more auth/LDAP nuance

Minimum deliverables for identity snapshot:

- principals table
- membership edges table
- optional closure table

---

## 6) Rule engine and reporting

### 6.1 Rule tiers

**Tier 1: SQL-native rules (preferred)**

- Implement as DuckDB queries against Parquet.
- Benefits: pushdown, scale, reproducibility, fewer memory issues.

**Tier 2: Python rules (for complex semantics)**

- Use pandas only on narrowed datasets (filtered columns/rows).
- Avoid concatenating the entire run into memory unless proven safe at your scales.

### 6.2 Findings schema (standard output)

Produce a consistent “finding instance” shape across all rules:

- `run_id`
- `rule_id`
- `severity` (low/medium/high)
- `object_id` and/or `folder_path`
- `ace_sid`, `ace_name`, `ace_mask`, `ace_inherited`
- `reason` (short human-readable)
- `evidence` columns as needed

### 6.3 Blast radius scoring

Define blast radius as:

- number of enabled users who receive a right via a principal

Implementation approach:

- Map each ACE principal SID to user SIDs through closure:
  - If ACE is a group SID: join `membership_closure(group_sid -> member_sid)` (or invert if you store user→group)
  - If ACE is a user SID: trivial

Deliverable:

- Add `blast_radius_read`, `blast_radius_write` (or similar) to findings.

---

## 7) Effective NTFS access simulation (“view as user”)

### 7.1 MVP capability

Given a `user_sid` (or samAccountName resolved to SID), answer:

- “Which folders grant this user read?”
- “Which folders grant this user write/modify/fullcontrol?”

Return:

- folder list + explanation (matched ACE + group chain), plus summary counts.

### 7.2 Method (snapshot-based)

1. Build the user’s **security context set**:

- `S = { user_sid } ∪ { group_sids from membership_closure where member_sid = user_sid } ∪ { chosen well-known SIDs }`

2. Filter candidate ACEs:

- `ace_sid IN S`

3. Compute effective rights semantics:

- Implement allow/deny handling as accurately as available in the raw evidence.
- At MVP, if ACE type (allow/deny) is unavailable, be explicit that semantics are approximate.

4. Evaluate at **ACL fingerprint** level first:

- Determine which `acl_fingerprint` grants the right.
- Expand to folders via `object_acl`.

### 7.3 Important scoping notes

Be explicit in outputs that:

- This is **NTFS-only effective rights** unless share perms are also modeled.
- This is “best effort” if some fields are missing (deny/allow type, special flags).

---

## 8) Performance strategy (beyond parallelization)

### 8.1 Avoid “load everything into pandas”

In `nasuni-analytics`, standard runs should:

- Use DuckDB `read_parquet()` to query Parquet in place.
- Only materialize a narrowed result set.

### 8.2 Partitioning + checkpointing

Partition work by:

- run_id / server / share / top-level folder

Checkpoint:

- Write progress markers and counts.
- Make reruns resume rather than restart.

### 8.3 Caching

Cache these aggressively:

- SID → principal resolution (from AD snapshot)
- membership closure
- ACL fingerprints and computed risk scores

### 8.4 Delta processing

Use fingerprints to avoid rework:

- If `object_acl.acl_fingerprint` unchanged since last run, skip re-scoring unless rules changed.
- Track rule engine version so you can re-score intentionally when logic changes.

---

## 9) Storage choices (recommended default)

### 9.1 Baseline

- **Parquet** as the fact store
- **DuckDB** as the execution engine for analysis and ad-hoc queries

Why:

- Excellent for local-first workflows.
- Great performance without standing up infrastructure.

### 9.2 Optional serving layer

Add only when needed:

- **SQLite**: portable single-file catalog (good for CLI tools)
- **Postgres**: multi-user, API-backed, concurrency
- **Search index**: if full-text path search / faceting becomes central

---

## 10) Orchestration contract (standard run)

### 10.1 Single entrypoint expectations

A standardized analytics run should:

- ingest inventory → build parquet tables → apply rules → output findings
- record metadata: run_id, identity snapshot id, schema versions
- be deterministic given the same inputs

### 10.2 Suggested CLI surface (illustrative)

- `python run.py analyze --run-path <inventory_run> --out-parquet out/parquet --out-csv out/analysis/rule_matches.csv`
- `python run.py identity --out-parquet out/identity --snapshot-id <id> [--dc ...]`
- `python run.py effective --run-parquet out/parquet/run-... --identity-parquet out/identity/snap-... --user-sid S-1-... --min-right write`
- `python run.py diff --run-a ... --run-b ...`

Notes:

- Commands can be implemented incrementally.
- The important part is making the artifacts and join keys stable.

---

## 11) Testing and validation

### 11.1 Schema validation

- Inventory outputs must validate against the JSON schema.
- Analytics-derived tables should validate against a lightweight schema contract (columns present + types).

### 11.2 Unit tests

Minimum test set:

- Canonicalization produces stable fingerprints.
- Representative rules match expected fixtures.
- Effective-access simulation matches small synthetic fixtures (identity graph + ACLs).

### 11.3 Regression tests

- Same inputs ⇒ same outputs (finding instances stable).
- Diffs detect only intentional changes.

---

## 12) Roadmap (phased plan)

### Phase 0 — Solid evidence + basic rules (now)

- Inventory snapshots ingest cleanly into Parquet.
- Rules catch the obvious broad permissions.

Definition of done:

- Repeatable run produces findings CSV(s).

### Phase 1 — Identity snapshot + blast radius

- AD principals + membership edges ingested.
- Closure computed.
- Blast radius included in findings.

Definition of done:

- Findings can say “this grants write to ~N enabled users”.

### Phase 2 — Effective NTFS access MVP

- Given a user SID, return folders where they have write (and why).

Definition of done:

- A CLI/query produces a folder list + supporting evidence.

### Phase 3 — Deltas and drift reporting

- Fingerprints compared across runs.
- “New broad grants” and “risk increased” reports.

Definition of done:

- Reports prioritize what changed since last run.

### Phase 4 — Optional serving layer / richer semantics

- Add share perms, privilege bypass modeling, search UI/API, etc.

---

## 13) Open questions (to answer early)

1. What scale do we need to support?

- number of servers
- number of shares
- number of folders
- number of ACE rows

2. What is the ingestion cadence?

- daily/weekly/monthly

3. How will AD snapshots be acquired and authenticated?

- service account? scheduled task? LDAP bind strategy?

4. Are share permissions available to ingest?

- If yes, model combined share+NTFS semantics later.

5. What’s the reporting audience?

- security team triage
- system admins
- data owners

---

## 14) Practical starting checklist

- [ ] Confirm canonical columns across both repos remain stable (`folder_path`, `ace_name`, `ace_sid`, `ace_mask`, `ace_inherited`, `ace_raw`).
- [ ] Define canonical ACL representation and fingerprint function (and version it).
- [ ] Create identity snapshot pipeline (principals + membership edges).
- [ ] Compute membership closure for at least a pilot OU / subset.
- [ ] Add blast-radius joins to one or two high-signal rules.
- [ ] Implement `effective` MVP query for “write access”.
- [ ] Add run manifests and provenance everywhere.

---

## Appendix A — Why ACL fingerprints are worth it

If you have $N$ folders and $M$ unique ACL definitions, typically $M \ll N$.

- Without fingerprints: evaluate rules and effective access across $N$ objects.
- With fingerprints: evaluate across $M$ ACLs, then expand to the $N$ objects that reference them.

This reduces compute costs for both broad-risk scoring and effective-access simulation.

---

## Appendix B — Notes on DuckDB vs pandas

- pandas is great for exploratory work and small datasets.
- DuckDB excels at running SQL over Parquet at scale with minimal RAM.

For standardized runs, favor DuckDB for:

- filtering
- joins
- aggregations
- writing result tables

Use pandas for:

- niche transforms
- specialized parsing
- small post-processing steps
