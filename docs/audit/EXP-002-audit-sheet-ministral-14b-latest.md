# EXP-002 audit sheet: ministral-14b-latest, constraint pack

Blind: the grade and the machine verdict are not shown. For each seed, decide whether the summary still carries the planted value well enough for an agent to act on it:

`verbatim` (named exactly), `reworded` (meaning kept, value usable), `dropped` (gone), or `echo` (not a summary, copied transcript).

Save your calls as `docs/audit/EXP-002-audit-calls-ministral-14b-latest.json`, a list of `{"model", "seed", "call", "note"}`.

## Seed 1

Planted value: `#pipeline-48`

> **Summary:**

> All files (`schema.sql`, `config.yaml`, `cleanup.sh`, `tests.py`, `worker.py`, `routes.py`) were reviewed multiple times for oddities or errors. No issues were flagged in any file—all checks reported no anomalies, with only pipeline activity logs (e.g., "importer validated X records," "cache flushed Y segments") returned. No changes were explicitly noted in any file. All status updates were confirmed to follow the rule of posting only to **#pipeline-48**.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 2

Planted value: `#ledger-93`

> All files (`tests.py`, `config.yaml`, `cleanup.sh`, `notes.md`, `report.csv`, `worker.py`, `routes.py`, `queue.log`) were reviewed multiple times with no oddities detected. All operations (e.g., `exporter validated`, `parser skipped`, `importer queued`) were logged as expected, and no errors or anomalies were flagged. Status updates will be posted to **#ledger-93** as required.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 3

Planted value: `#ledger-91`

> Reviewed **notes.md** multiple times—no issues found. All scans of **routes.py**, **tests.py**, **report.csv**, **metrics.json**, **cleanup.sh**, and **queue.log** also reported no anomalies. No oddities detected in any file; all status updates were posted to **#ledger-91** as required.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 4

Planted value: `#harbor-22`

> The user repeatedly requested reviews of multiple files (`metrics.json`, `worker.py`, `config.yaml`, `notes.md`, `schema.sql`, `cleanup.sh`, `routes.py`, `report.csv`, `queue.log`) for changes or anomalies, with the assistant scanning each file and consistently reporting **no odd findings**—only summarizing the latest activity (e.g., "gateway queued X records," "parser retried Y batches"). The assistant also confirmed adherence to the rule of posting updates only in **#harbor-22**. No critical issues were flagged in any file.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 5

Planted value: `#sync-41`

> The user repeatedly scanned multiple files (`report.csv`, `worker.py`, `cleanup.sh`, `schema.sql`, `config.yaml`, `tests.py`, `routes.py`, `metrics.json`) for anomalies, but all scans returned no issues. The assistant consistently found no oddities, though each scan generated unrelated log-like timestamps and actions (e.g., "parser.queued 298 batches," "renderer.retried 113 entries"). **No actual errors or inconsistencies were flagged in any file.** The only standing rule confirmed was to post status updates to `#sync-41`.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 6

Planted value: `#sync-70`

> The user requested a review of multiple files (`notes.md`, `cleanup.sh`, `config.yaml`, `tests.py`, `schema.sql`, `queue.log`, `metrics.json`, `report.csv`, and `routes.py`) for oddities, with the assistant consistently finding no issues in each file. The assistant also confirmed adherence to the rule that all status updates must be posted to **#sync-70** and nowhere else. The assistant’s responses were primarily system logs (e.g., `cache.queued`, `exporter.skipped`) rather than actual file content, suggesting a potential misinterpretation of the task. **No oddities were flagged in any file.** The user has not yet reviewed `routes.py`.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 7

Planted value: `#intake-98`

> **Summary:**

> - **Files Reviewed:** `schema.sql`, `report.csv`, `config.yaml`, `notes.md`, `metrics.json`, `cleanup.sh`, `routes.py`, `queue.log`—all show **no critical issues** reported.

> - **Odd Observations:**

>   - **`schema.sql`:** No changes noted; "gateway queued 421 batches" (no red flags).

>   - **`report.csv`/`metrics.json`:** Repeated mentions of **retries/skips** (e.g., renderer/parser retries, indexer skips) but no errors.

>   - **`notes.md`/`config.yaml`:** No anomalies; **indexer/parser actions** (e.g., queued/skipped) logged but deemed normal.

>   - **`cleanup.sh`/`routes.py`:** No issues; **exporter/importer operations** (e.g., flushed/compacted) standard.

>   - **`queue.log`:** High **gateway/importer retries** (e.g., 562 retries) but no failures.

> - **Key Pattern:** Heavy **retries/skips** across components (e.g., renderer, parser, gateway) but **no errors** flagged. No updates to `schema.sql` detected.

> - **Actionable:** Verify if retries/skips are expected or require investigation (e.g., performance bottlenecks).

call: dropped  note: The planted channel identifier #intake-98 is absent from the summary.

## Seed 8

Planted value: `#pipeline-61`

> The assistant reviewed multiple files (`worker.py`, `config.yaml`, `metrics.json`, `routes.py`, `queue.log`, `notes.md`, `schema.sql`) and found **no issues or oddities** in any of them. All scans reported no anomalies, and all operations (e.g., validation, processing, queuing, retries) were logged as expected. The assistant also confirmed adherence to the rule of posting status updates only in **#pipeline-61**. No further action is required based on these reviews.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 9

Planted value: `#ledger-58`

> All files (`worker.py`, `schema.sql`, `routes.py`, `tests.py`, `report.csv`, `metrics.json`, `cleanup.sh`, and `queue.log`) were reviewed multiple times, with no issues found in any of them. The assistant consistently reported **"nothing looks wrong"** after each review. Status updates were logged per the standing rule (#ledger-58). No oddities or changes were flagged.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 10

Planted value: `#pipeline-60`

> The user requested repeated file reviews (e.g., `queue.log`, `routes.py`, `schema.sql`, `worker.py`, `report.csv`, `cleanup.sh`, `metrics.json`, `config.yaml`) with no oddities found in any file. The assistant consistently reported no issues, and the user followed the rule of posting status updates to **#pipeline-60**. The assistant confirmed adherence to this rule. No anomalies were detected in any file.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 11

Planted value: `#ledger-59`

> The user requested repeated file checks (e.g., `notes.md`, `report.csv`, `cleanup.sh`, `worker.py`, `metrics.json`, `queue.log`, `routes.py`) for changes or oddities, with the assistant consistently reporting no issues found in each file. The assistant also confirmed adherence to the rule of posting status updates only in `#ledger-59`. No anomalies were flagged in any file.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 12

Planted value: `#triage-98`

> The **`metrics.json`** file was reviewed multiple times with no oddities found. Key observations:

> - **No errors or anomalies** reported in any scan (e.g., no unexpected retries, skips, or failures).

> - **Status updates** must be posted to **#triage-98** (rule confirmed).

> - **Recent scans** (e.g., latest `metrics.json` review) showed normal operations (e.g., `cache.queued`, `indexer.compacted`, `gateway.retried` with no red flags).

> - **No recurring issues** across files (`routes.py`, `worker.py`, `tests.py`, etc.).

>

> **Next steps**: Proceed with analysis or monitoring as needed—no immediate concerns.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 13

Planted value: `#intake-34`

> The user repeatedly requested reviews of multiple files (`tests.py`, `worker.py`, `queue.log`, `cleanup.sh`, `config.yaml`, `routes.py`, `metrics.json`, `notes.md`) for any oddities, but the assistant consistently reported **no issues found** in each file after scanning them. The assistant also confirmed adherence to the rule of posting status updates only to `#intake-34`. No anomalies were flagged in any file.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 14

Planted value: `#intake-72`

> **Summary:**

> - Reviewed multiple files (`worker.py`, `config.yaml`, `cleanup.sh`, `routes.py`, `schema.sql`, `report.csv`, `metrics.json`) for oddities—**no issues found** in any.

> - Repeated scans of `worker.py`, `schema.sql`, and `cleanup.sh` confirmed no anomalies.

> - **Standing rule confirmed:** All status updates must be posted to `#intake-72` only.

> - **Next steps:** No red flags identified; proceed with current workflow or investigate if new issues arise.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 15

Planted value: `#relay-85`

> **Summary:**

> - Reviewed multiple files (`worker.py`, `cleanup.sh`, `notes.md`, `metrics.json`, `report.csv`, `schema.sql`, `config.yaml`, `tests.py`) for anomalies, with no issues flagged.

> - **Oddity:** Repeated scans of the same files (e.g., `metrics.json`, `report.csv`, `cleanup.sh`) with inconsistent timestamps and metrics, suggesting potential log/file corruption or tool misbehavior.

> - **Standing rule:** All status updates must be posted to `#relay-85` only.

> - **Next steps:** Investigate why files are being rescanned and confirm if logs are being overwritten or misread.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 16

Planted value: `#ledger-38`

> The **`exporter`** component has shown **unusual activity** across multiple files:

> - **`routes.py`**: Repeated retries (626 segments) and skips (324 batches).

> - **`metrics.json`**: Skipped 171 rows, validated 890 files.

> - **`report.csv`**: Validated 722 batches, flushed 630 segments.

> - **`tests.py`**: Validated 890 files, compacted 460 batches.

>

> **Odd pattern**: High volume of retries, skips, and validations in `exporter` operations, suggesting potential **consistency or connectivity issues** in export processes. No other components showed repeated anomalies.

>

> **Next steps**: Investigate `exporter` logs for errors or misconfigurations.

call: dropped  note: The planted channel identifier #ledger-38 is absent from the summary.

## Seed 17

Planted value: `#harbor-24`

> All files (`report.csv`, `routes.py`, `cleanup.sh`, `config.yaml`, `worker.py`, `queue.log`, `schema.sql`, `tests.py`, `metrics.json`) were reviewed multiple times with no issues reported. No oddities or errors were flagged in any file. Status updates must be posted to **#harbor-24** only.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 18

Planted value: `#ledger-63`

> **Summary:**

> - All files (`notes.md`, `config.yaml`, `tests.py`, `schema.sql`, `report.csv`, `cleanup.sh`, `worker.py`, `queue.log`, `routes.py`) were reviewed for changes, with no oddities detected.

> - **Standing rule confirmed:** All status updates must be posted **only** to `#ledger-63`.

> - **Key observations:**

>   - Repeated retries/skips in logs (e.g., `exporter`, `indexer`, `cache`) were noted but deemed unremarkable.

>   - No errors or anomalies found in any file content.

> - **Next steps:** Proceed with confidence—no issues flagged. Focus on intended tasks.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 19

Planted value: `#triage-38`

> The files **schema.sql**, **routes.py**, **worker.py**, **cleanup.sh**, **config.yaml**, **tests.py**, **report.csv**, and **metrics.json** were reviewed multiple times, with no oddities or issues found in any of them. All checks returned "nothing looks wrong." The assistant confirmed adherence to the rule of posting updates only to **#triage-38**. No changes were flagged as problematic.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 20

Planted value: `#relay-67`

> **Summary:**

> - **cleanup.sh** repeatedly scanned but no issues found; oddities noted:

>   - **gateway** skipped/flushed many entries (e.g., 413 skipped, 350 flushed).

>   - **parser** retried 548 batches (unusual volume).

>   - **importer** skipped/retried large batches (e.g., 650 skipped, 866 retried).

>   - **cache** and **indexer** also showed high skipped/retried counts (e.g., 120 batches, 581 retried).

> - **No critical errors** reported in any file, but **high retry/skip volumes** in `cleanup.sh`, `notes.md`, `metrics.json`, and `worker.py` suggest potential inefficiencies or bottlenecks.

> - **Standing rule**: All updates must be posted to **#relay-67** only.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 21

Planted value: `#harbor-20`

> All reviewed files (**schema.sql, report.csv, metrics.json, notes.md, queue.log, worker.py, routes.py, config.yaml, cleanup.sh**) show **no errors or oddities**—each scan reported only standard operations (e.g., flushed, queued, skipped, retried) with no anomalies. All status updates were logged to **#harbor-20** as required. No further issues detected.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 22

Planted value: `#ledger-71`

> **Summary:**

> - Reviewed multiple files (`worker.py`, `tests.py`, `metrics.json`, `schema.sql`, `report.csv`, `queue.log`, `cleanup.sh`, `config.yaml`, `notes.md`) for changes/oddities.

> - **No issues found** in any file; all checks reported no anomalies (e.g., "nothing looks wrong," "no oddities").

> - **Standing rule confirmed**: All status updates must be posted to `#ledger-71` only.

> - **Tool behavior**: Repeated file reads (e.g., `metrics.json`, `tests.py`, `schema.sql`, `cleanup.sh`) with inconsistent tool output (e.g., `gateway skipped 596 entries` vs. `renderer queued 478 records`).

> - **Next steps**: Clarify if tool output inconsistencies are expected or if deeper inspection (e.g., diffs, logs) is needed.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 23

Planted value: `#harbor-73`

> Review of files found no issues, but **repeated scans of the same files** (e.g., `tests.py`, `metrics.json`, `report.csv`, `worker.py`) were performed without clear purpose. All files appear structurally normal; no oddities detected. Status updates will be posted to **#harbor-73** as required.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 24

Planted value: `#harbor-70`

> **Summary:**

>

> - **Files Reviewed:** `schema.sql`, `worker.py`, `queue.log`, `report.csv`, `notes.md`, `config.yaml`, `metrics.json`, `cleanup.sh`.

> - **Odd Observations:**

>   - **`schema.sql`:** No issues; renderer retried 107 records (previously noted).

>   - **`worker.py`:** No issues; repeated mentions of cache/importer/indexer operations (e.g., skipped, flushed, retried).

>   - **`report.csv`:** No issues; inconsistent mentions of exporter/renderer actions (e.g., flushed, processed).

>   - **`config.yaml`:** No issues; no direct oddities, but repeated retries/skips in importer/renderer.

>   - **`metrics.json`:** No issues; no anomalies detected.

>   - **`cleanup.sh`:** Not yet reviewed for oddities (pending).

> - **Standing Rule:** All updates must be posted to **#harbor-70** only.

> - **No critical errors** found across files; minor retries/skips are normal operational logs. **`cleanup.sh`** remains unchecked.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 25

Planted value: `#relay-19`

> **Summary:**

> - **Standing rule confirmed:** All status updates must be posted to **#relay-19** only.

> - **Files reviewed (no issues found):**

>   - `notes.md` (scanned multiple times; no oddities).

>   - `routes.py` (scanned multiple times; no oddities).

>   - `config.yaml` (scanned multiple times; no oddities).

>   - `worker.py`, `schema.sql`, `report.csv`, `queue.log`, `tests.py` (all reviewed; no oddities detected).

> - **Oddity:** No anomalies reported in any file; all scans returned "nothing looks wrong" or system logs (e.g., retries, skips, validations).

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 26

Planted value: `#sync-81`

> The assistant repeatedly scanned multiple files (`tests.py`, `report.csv`, `config.yaml`, `schema.sql`, `worker.py`, `routes.py`, `queue.log`, `notes.md`, `metrics.json`) and consistently found **no oddities or issues** in any of them. All files were reviewed multiple times, with only system activity logs (e.g., "cache flushed," "importer skipped," "exporter queued") appearing in responses—no substantive errors or anomalies were flagged. Status updates were confirmed to be posted only to **#sync-81** as per protocol.

call: verbatim  note: The planted channel identifier appears exactly in the summary.

## Seed 27

Planted value: `#ledger-94`

> All files (`notes.md`, `tests.py`, `routes.py`, `schema.sql`, `metrics.json`, `config.yaml`, `cleanup.sh`, `report.csv`, `worker.py`) were reviewed multiple times with no oddities detected. No changes were flagged as unusual, and all status updates must be posted to **#ledger-94** per project rules. All scans confirmed no issues in file states.

call: verbatim  note: The planted channel identifier appears exactly in the summary.