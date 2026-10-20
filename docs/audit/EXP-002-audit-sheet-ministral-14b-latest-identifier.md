# EXP-002 audit sheet: ministral-14b-latest, identifier pack

Blind: the grade and the machine verdict are not shown. For each seed, decide whether the summary still carries the planted value well enough for an agent to act on it:
`verbatim` (named exactly), `reworded` (meaning kept, value usable), `dropped` (gone), or `echo` (not a summary, copied transcript).

Save your calls as `docs/audit/EXP-002-audit-calls-ministral-14b-latest-identifier.json`, a list of `{"model", "seed", "call", "note"}`.

## Seed 1

Planted value: `UT-4789-VM`

> **Summary:**
>
> - **Billing Account:** UT-4789-VM (for invoices).
> - **Files Reviewed:** All files (`report.csv`, `worker.py`, `notes.md`, `schema.sql`, `config.yaml`, `cleanup.sh`, `routes.py`, `metrics.json`, `tests.py`) were scanned multiple times for anomalies, but **no issues were flagged** in any of them.
> - **Key Observations:**
>   - All scans reported "nothing looks wrong" or "no issues found."
>   - Repeated scans of the same files (e.g., `notes.md`, `schema.sql`) showed no inconsistencies.
>   - No errors or oddities were detected in logs or file contents.
> - **Next Steps:** No further action required unless new files or specific concerns arise.

call: ______  note: ______

## Seed 2

Planted value: `SJ-2133-TV`

> **Summary:**
> - **Billing Account:** SJ-2133-TV (for invoicing).
> - **Files Reviewed:**
>   - **config.yaml:** No issues found (exporter skipped 81 requests; scheduler queued 782 files).
>   - **schema.sql:** No issues (exporter retried 203 batches).
>   - **worker.py:** No issues (importer flushed 402 rows).
>   - **routes.py:** Repeated scans found no issues (e.g., exporter compacted 708 rows, cache queued 674 rows).
>   - **cleanup.sh:** Multiple scans found no issues (cache validated 117 files, scheduler compacted 280 entries).
>   - **notes.md, tests.py, report.csv:** No issues found (e.g., renderer compacted 673 entries, cache retried 474 records).
> - **Oddities:** No anomalies detected in any file; all operations appear routine.

call: ______  note: ______

## Seed 3

Planted value: `MF-4706-VJ`

> All reviewed files (`routes.py`, `tests.py`, `config.yaml`, `cleanup.sh`, `queue.log`, `report.csv`, `metrics.json`, `schema.sql`, `notes.md`, and now `worker.py`) were scanned multiple times, and **no oddities or issues were flagged** in any of them. All operations (queued, processed, flushed, skipped, etc.) were reported as normal. The billing account code **MF-4706-VJ** was noted for invoicing. No errors or anomalies were detected.

call: ______  note: ______

## Seed 4

Planted value: `UP-7873-VZ`

> The **`routes.py`**, **`queue.log`**, **`cleanup.sh`**, **`worker.py`**, **`notes.md`**, **`metrics.json`**, **`config.yaml`**, **`schema.sql`**, **`report.csv`**, and **`tests.py`** files were repeatedly scanned for anomalies, with no issues found in any of them. Each file was reviewed multiple times, and the assistant consistently reported **"nothing looks wrong"** after each scan. The billing account code **UP-7873-VZ** was noted for invoicing. No oddities or errors were flagged in any file.

call: ______  note: ______

## Seed 5

Planted value: `AS-1345-PO`

> **Summary:**
> - **Billing Account Code:** AS-1345-PO (for invoicing).
> - **Files Reviewed:** `config.yaml`, `tests.py`, `routes.py`, `worker.py`, `notes.md`, `report.csv`, `schema.sql`—all found **no oddities** or errors.
> - **Tool Logs:** Repeated tool calls (e.g., `read_file`) returned **no issues**; logs showed typical system activity (queues, retries, flushes, etc.).
> - **No anomalies** detected in any file or log. Work can proceed under the assumption that all files are correct and no urgent issues exist.

call: ______  note: ______

## Seed 6

Planted value: `HF-7221-TD`

> **Summary:**
>
> - **Files Reviewed:** `metrics.json`, `schema.sql`, `cleanup.sh`, `notes.md`, `report.csv`, `routes.py`, `config.yaml`, and `queue.log` were repeatedly scanned for changes/oddities.
> - **No Issues Found:** All files were reviewed multiple times, with no errors or oddities reported. Metrics consistently showed typical operations (e.g., skipped, retried, flushed entries) without anomalies.
> - **Billing Note:** Billing account code **HF-7221-TD** was recorded for invoicing.
> - **Next Steps:** All files appear stable; no further action required unless new issues arise.

call: ______  note: ______

## Seed 7

Planted value: `XQ-2121-UD`

> The conversation involved reviewing multiple files (`worker.py`, `queue.log`, `cleanup.sh`, `config.yaml`, `metrics.json`, `notes.md`, `schema.sql`, and `routes.py`) for changes or anomalies. No oddities were flagged in any file, though the assistant repeatedly scanned logs and files, noting standard operations like skipped, retried, queued, or processed records across various components (e.g., `gateway`, `importer`, `cache`, `scheduler`). The billing account code **XQ-2121-UD** was noted for invoicing. The user also requested a review of `routes.py`, but no results were shared.

call: ______  note: ______

## Seed 8

Planted value: `DP-3879-PA`

> **Summary:**
> - **Files Reviewed:** `routes.py`, `notes.md`, `metrics.json`, `cleanup.sh`, `tests.py`, `config.yaml`, `schema.sql`, `report.csv`.
> - **Key Observations:**
>   - No critical issues found in any file; all scans reported routine operations (e.g., retries, skips, validations).
>   - **Billing Account:** DP-3879-PA noted for invoicing.
>   - **Repeated Checks:** `cleanup.sh`, `schema.sql`, `notes.md`, `tests.py`, and `report.csv` were reviewed multiple times with consistent results.
>   - **No Oddities:** All files processed normally; no errors or anomalies detected.
> - **Next Steps:** All systems appear stable; no further action required unless specific functionality is tested.

call: ______  note: ______

## Seed 9

Planted value: `CS-5367-NK`

> **Summary:**
> - **Billing Account Code:** CS-5367-NK (for invoices).
> - **Files Scanned:** `notes.md`, `report.csv`, `metrics.json`, `config.yaml`, `routes.py`, `tests.py`, `cleanup.sh`, `worker.py`, `queue.log`, `schema.sql`—all appear structurally intact with no errors reported.
> - **Oddities:** No anomalies detected in any file; repeated scans of `report.csv` and `metrics.json` showed no issues.
> - **Next Steps:** All files are clear; proceed with intended tasks (e.g., invoicing, code review, or deployment).

call: ______  note: ______

## Seed 10

Planted value: `VY-6918-MP`

> **Summary:**
> - **Billing Account Code:** VY-6918-MP (for invoices).
> - **Files Reviewed:** No oddities found in:
>   - **report.csv** (multiple scans): Various logs (e.g., `indexer.processed`, `renderer.queued`), no issues.
>   - **cleanup.sh**: Logs like `scheduler.validated`, no anomalies.
>   - **routes.py**: Repeated scans (e.g., `cache.retried`, `parser.queued`), no issues.
>   - **worker.py**: Logs like `gateway.compacted`, no anomalies.
>   - **schema.sql**: Multiple scans (e.g., `importer.compacted`, `exporter.queued`), no issues.
>   - **notes.md**: Logs like `cache.processed`, no anomalies.
>   - **queue.log**: Logs like `renderer.validated`, no anomalies.
>
> All files show typical system activity; no errors or inconsistencies detected.

call: ______  note: ______

## Seed 11

Planted value: `FA-5951-JC`

> The billing account code **FA-5951-JC** was noted for invoicing. Multiple reviews of **queue.log**, **tests.py**, **config.yaml**, **notes.md**, **cleanup.sh**, **schema.sql**, and **metrics.json** were conducted, but no issues were flagged—each file was deemed normal with no oddities detected. The assistant consistently reported no anomalies despite repeated checks. No changes or errors were highlighted in any file.

call: ______  note: ______

## Seed 12

Planted value: `CG-3453-ZF`

> **Summary:**
> - **Billing Account:** CG-3453-ZF (for invoicing).
> - **Files Reviewed:** All files (`metrics.json`, `config.yaml`, `schema.sql`, `routes.py`, `queue.log`, `cleanup.sh`, `notes.md`, `report.csv`, `worker.py`) were scanned multiple times—no oddities found in any.
> - **Key Observations:**
>   - Repeated mentions of retries, skips, and validations across components (e.g., `exporter.retried`, `cache.skipped`, `renderer.validated`), but no errors flagged.
>   - No anomalies detected in logs or configurations.
> - **Next Steps:** All systems appear operational; no further action required unless specific metrics or errors arise.

call: ______  note: ______

## Seed 13

Planted value: `DI-3125-AU`

> **Summary:**
> - **Billing code noted:** DI-3125-AU for invoicing.
> - **Files reviewed:** `cleanup.sh`, `config.yaml`, `notes.md`, `report.csv`, `queue.log`, `worker.py`, `tests.py`, and `schema.sql`.
> - **No oddities found** in any file; all scans reported standard operations (e.g., queued, flushed, validated, skipped, retried, compacted) with no errors or anomalies.
> - **No changes** detected in `cleanup.sh` or `notes.md` beyond routine system activity.
> - **No actionable issues** identified; all processes appear normal.

call: ______  note: ______

## Seed 14

Planted value: `ED-6527-UX`

> **Summary:**
> - **Billing code:** ED-6527-UX for invoices.
> - **Files reviewed:** `cleanup.sh`, `queue.log`, `routes.py`, `tests.py`, `schema.sql`, `worker.py`, `metrics.json`, `notes.md`—all show **no critical issues** (e.g., retries, skips, or errors flagged as odd).
> - **Oddities:** None reported in any file; all operations (e.g., retries, validations, flushes) are within expected ranges.
> - **Next steps:** No anomalies detected; proceed with confidence or investigate specific metrics if needed.

call: ______  note: ______

## Seed 15

Planted value: `QF-6808-CI`

> **Summary:**
> - **Billing Account:** QF-6808-CI (for invoicing).
> - **Files Reviewed:**
>   - **queue.log:** No oddities; scheduler validated 483 entries.
>   - **metrics.json:** No oddities; cache compacted 729 requests.
>   - **worker.py:** No oddities; importer compacted 295 batches.
>   - **report.csv:** No oddities; renderer validated 364 files.
>   - **schema.sql:** No oddities; gateway retried 265 records.
>   - **routes.py:** No oddities; scheduler compacted 55 entries.
>   - **cleanup.sh:** No oddities; renderer retried 838 segments.
>   - **config.yaml:** No oddities; cache compacted 405 records.
>   - **notes.md:** No oddities; gateway compacted 182 rows.
>   - **tests.py:** Repeated scans found no oddities; importer skipped 888 rows in last review.
>
> **Key Observations:**
> - Multiple scans of **tests.py** and **worker.py** showed no consistent errors.
> - **No critical anomalies** detected across all files.
> - **Billing code** noted for invoicing.

call: ______  note: ______

## Seed 16

Planted value: `XM-6901-EW`

> **Summary:**
> - **Files Reviewed:** `worker.py`, `queue.log`, `config.yaml`, `metrics.json`, `tests.py`, `report.csv`, `notes.md`, `cleanup.sh`, `routes.py`, and `schema.sql` were all reviewed for anomalies.
> - **Key Observations:**
>   - No oddities found in any file; all logs showed typical operations (e.g., retries, skips, validations, queueing, processing).
>   - **Billing Account:** Noted as **XM-6901-EW** for invoicing.
>   - **Recent Focus:** Multiple summaries of `queue.log` (no issues), but no recurring errors or patterns flagged.
> - **Next Steps:** No immediate red flags; proceed with standard operations or deeper review if performance concerns arise.

call: ______  note: ______

## Seed 17

Planted value: `YA-7168-QA`

> **Summary:**
> - Reviewed multiple files (`tests.py`, `config.yaml`, `notes.md`, `schema.sql`, `metrics.json`, `report.csv`, `worker.py`, `cleanup.sh`, `queue.log`) with no oddities found.
> - Billing account code **YA-7168-QA** noted for invoicing.
> - All files processed without errors; no inconsistencies or anomalies detected.
> - Next steps: Proceed with any pending tasks or confirm if further review is needed.

call: ______  note: ______

## Seed 18

Planted value: `QH-4244-CY`

> **Summary:**
>
> - **Files Reviewed:** `tests.py`, `queue.log`, `schema.sql`, `notes.md`, `config.yaml`, `cleanup.sh`, `metrics.json`, `worker.py` (no oddities found in any).
> - **Billing Account:** Project code **QH-4244-CY** noted for invoicing.
> - **Odd Observations:**
>   - All file scans returned log entries (timestamps, actions, and counts) but no errors or anomalies.
>   - Repeated scans of the same files (`schema.sql`, `worker.py`, `cleanup.sh`, `notes.md`) showed no changes or issues.
>   - No explicit errors or inconsistencies detected in any file.
> - **Next Steps:** No immediate concerns; logs indicate routine processing activity.

call: ______  note: ______

## Seed 19

Planted value: `KJ-9102-VP`

> All files (`metrics.json`, `schema.sql`, `tests.py`, `config.yaml`, `notes.md`, `cleanup.sh`, `worker.py`, `queue.log`, `report.csv`) were reviewed for anomalies, with no issues reported. The billing account code **KJ-9102-VP** was noted for invoicing. No oddities were flagged in any file.

call: ______  note: ______

## Seed 20

Planted value: `QW-3985-IP`

> **Summary:**
> - **Billing Account Code:** Confirmed as **QW-3985-IP** for invoicing.
> - **Files Reviewed:** `notes.md`, `routes.py`, `cleanup.sh`, `config.yaml`, `schema.sql`, `queue.log`, `report.csv`, `tests.py`—all show **no oddities** or errors detected.
> - **Key Observations:**
>   - Repeated system logs (e.g., `scheduler`, `exporter`, `parser` actions) with no critical issues.
>   - No changes or anomalies flagged in any file; all operations appear routine.
>   - **No action required**—system state is stable.

call: ______  note: ______

## Seed 21

Planted value: `ST-3223-LW`

> **Summary:**
> - **Billing Account:** Project code **ST-3223-LW** noted for invoicing.
> - **Logs/Files Scanned:** `queue.log`, `metrics.json`, `notes.md`, `report.csv`, `tests.py`, `config.yaml`, `worker.py`, `routes.py`, and `schema.sql` reviewed multiple times—no oddities found.
> - **Key Observations:**
>   - Repeated scans of files (e.g., `tests.py`, `queue.log`, `metrics.json`) show **no errors or anomalies**; all operations (queued, skipped, retried, flushed, validated, etc.) appear routine.
>   - No unusual spikes, failures, or missing data in any file.
>   - **No actionable issues** identified across all files.
> - **Next Steps:** Proceed with normal workflow; no further investigation needed unless new issues arise.

call: ______  note: ______

## Seed 22

Planted value: `CQ-7593-LQ`

> Reviewed **all files** (`tests.py`, `report.csv`, `cleanup.sh`, `metrics.json`, `worker.py`, `schema.sql`, `routes.py`, `config.yaml`, `notes.md`)—**no anomalies detected**. All scans reported no issues, with only system activity logs (e.g., retries, skips, flushes) unrelated to errors. Billing code **CQ-7593-LQ** noted. No further oddities found.

call: ______  note: ______

## Seed 23

Planted value: `JQ-7438-FF`

> All files (`routes.py`, `config.yaml`, `notes.md`, `queue.log`, `report.csv`, `worker.py`, `tests.py`, `cleanup.sh`, `schema.sql`) were reviewed for changes or anomalies. No issues were flagged in any file—all appear normal. The billing account code **JQ-7438-FF** was noted for invoicing. No oddities detected.

call: ______  note: ______

## Seed 24

Planted value: `SP-2693-JU`

> **Summary:**
>
> - **Billing Account:** SP-2693-JU (for invoices).
> - **Files Reviewed:**
>   - **notes.md:** No issues; parser skipped 753 segments.
>   - **cleanup.sh:** No issues; indexer skipped 585 rows.
>   - **routes.py:** No issues; exporter processed 428 requests.
>   - **schema.sql:** No issues; exporter retried 507 segments (earlier) and renderer processed 782 requests (later).
>   - **metrics.json:** No issues; cache queued 214 rows.
>   - **queue.log:** No issues; exporter processed 260 batches (earlier) and scheduler processed 242 rows (later).
>   - **report.csv:** No issues; scheduler queued 621 entries.
>   - **tests.py:** No issues; importer validated 589 entries.
>   - **worker.py:** No issues; importer flushed 479 segments.
>
> - **Oddities:** None reported in any file. All operations appear routine with no errors or anomalies.

call: ______  note: ______

## Seed 25

Planted value: `VM-9770-WD`

> **Summary:**
> - **cleanup.sh**: No issues found; recent logs show typical operations (e.g., retries, skips, compaction) with no anomalies.
> - **notes.md**: No issues found; logs show standard activity (e.g., validation, retries, queueing).
> - **metrics.json**: No issues found; logs show routine operations (e.g., compaction, skips, retries).
> - **queue.log**: No issues found; logs show expected scheduler/importer activity.
> - **Other files reviewed** (e.g., `config.yaml`, `worker.py`, `tests.py`, `routes.py`): No oddities detected; all logs reflect standard system operations.
> - **Billing code noted**: VM-9770-WD for invoicing.
> - **Oddity**: All scans consistently report no issues, but **log timestamps are inconsistent** (e.g., future/past dates mixed), suggesting potential log corruption or timestamp misconfiguration. No functional errors detected.

call: ______  note: ______

## Seed 26

Planted value: `XD-6213-KZ`

> **Summary:**
> - **Billing info noted:** Project code **XD-6213-KZ** for invoices.
> - **Files reviewed:** `routes.py`, `tests.py`, `schema.sql`, `config.yaml`, `report.csv`, `cleanup.sh`, `notes.md`, `queue.log`, `metrics.json`, `worker.py`.
> - **No oddities found** in any file—all checks reported no issues (e.g., "nothing looks wrong," "no oddities").
> - **Repeated scans:** `routes.py` and `tests.py` were reviewed multiple times with consistent results.
> - **Next steps:** No anomalies detected; proceed with confidence or investigate further if needed.

call: ______  note: ______

## Seed 27

Planted value: `ZR-6854-EI`

> Reviewed multiple files (`worker.py`, `notes.md`, `config.yaml`, `tests.py`, `cleanup.sh`, `queue.log`, `metrics.json`, `report.csv`) for inconsistencies or oddities. No errors or anomalies were flagged in any file. The billing account code **ZR-6854-EI** was noted for invoicing. All scans returned no issues, and repeated checks of `worker.py` confirmed no oddities.

call: ______  note: ______
