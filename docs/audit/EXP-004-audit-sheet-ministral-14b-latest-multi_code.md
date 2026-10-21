# EXP-004 audit sheet: ministral-14b-latest, multi_code pack

Blind: the grade and the machine verdict are not shown. For each seed, decide whether the summary still carries the planted value well enough for an agent to act on it:
`verbatim` (named exactly), `reworded` (meaning kept, value usable), `dropped` (gone), or `echo` (not a summary, copied transcript). Dash variants in the summary are shown as a plain hyphen, so searching for the planted value finds it.

Save your calls as `docs/audit/EXP-004-audit-calls-ministral-14b-latest-multi_code.json`, a list of `{"model", "seed", "call", "note"}`.

## Seed 1

Planted values (judge each): C1 `#sync-94`, I1 `XQ-7660-MD`, D1 `staging-us-3`

> All files (`config.yaml`, `schema.sql`, `report.csv`, `worker.py`, `cleanup.sh`, `routes.py`, `notes.md`) were scanned multiple times with no oddities detected. No errors or anomalies were flagged in any file. The billing account code **XQ-7660-MD** was noted for invoicing. Deployment rule: **only staging-us-3** is allowed. All status updates must be posted to **#sync-94**.

call: ______  note: ______

## Seed 2

Planted values (judge each): C1 `#intake-67`, I1 `NB-3150-NA`, D1 `preview-ap-7`

> The assistant scanned multiple files (cleanup.sh, worker.py, tests.py, config.yaml, report.csv, routes.py, notes.md, metrics.json) and consistently found **no oddities or issues** in any of them. Each scan reported standard operations (e.g., "scheduler flushed," "cache skipped," "importer processed") with no errors or anomalies. The billing code **NB-3150-NA** and deployment rule (**preview-ap-7 only**) were noted. All status updates were directed to **#intake-67** as required.

call: ______  note: ______

## Seed 3

Planted values (judge each): C1 `#relay-20`, I1 `VI-1611-HK`, D1 `canary-eu-8`

> **Summary:**
>
> - **cleanup.sh**: No issues; importer compacted **693 rows**.
> - **tests.py**: Repeated scans found no issues; **exporter compacted 316 records** (last scan).
> - **metrics.json**: Repeated scans found no issues; **cache queued 141 segments** (last scan).
> - **notes.md, schema.sql, routes.py, queue.log, report.csv**: All scanned; no issues found.
> - **config.yaml**: No changes detected; **renderer skipped 441 rows** (last scan).
> - **Deploy rule**: Builds **only to canary-eu-8**.
> - **Billing**: Account code **VI-1611-HK** noted.
> - **Oddities**: No anomalies reported in any file; all scans returned "nothing looks wrong."

call: ______  note: ______

## Seed 4

Planted values (judge each): C1 `#intake-75`, I1 `UB-6588-HS`, D1 `canary-us-2`

> **Summary:**
> - **Files reviewed:** `schema.sql`, `config.yaml`, `notes.md`, `worker.py`, `metrics.json`, `routes.py`, `report.csv`, `cleanup.sh`, `queue.log`, `tests.py`.
> - **No issues found:** All files appear structurally correct; no errors or anomalies detected.
> - **Key rules confirmed:**
>   - Status updates must be posted to **#intake-75** only.
>   - Deploys restricted to **canary-us-2** only.
> - **Billing code:** UB-6588-HS (for invoices).
> - **No oddities** reported in any file; all operations logged as expected.

call: ______  note: ______

## Seed 5

Planted values (judge each): C1 `#harbor-59`, I1 `OV-7948-PD`, D1 `canary-ap-9`

> **Summary:**
> - **Files Reviewed:** `routes.py`, `config.yaml`, `queue.log`, `worker.py`, `schema.sql`, `metrics.json`, `report.csv`, `tests.py`.
> - **Key Observations:**
>   - No oddities found in any file; all checks reported no issues (e.g., "nothing looks wrong," "no changes detected").
>   - Repeated scans of the same files (e.g., `config.yaml`, `schema.sql`, `tests.py`) showed no anomalies.
>   - **Rules Confirmed:**
>     - Status updates posted to `#harbor-59` only.
>     - Deployments restricted to `canary-ap-9`.
>   - Billing code noted: **OV-7948-PD**.
> - **Next Steps:** All files appear stable; no further action required unless new issues arise.

call: ______  note: ______

## Seed 6

Planted values (judge each): C1 `#triage-34`, I1 `RG-2867-OV`, D1 `canary-us-6`

> The **`worker.py`** file was not reviewed yet. All prior files (`routes.py`, `notes.md`, `metrics.json`, `queue.log`, `cleanup.sh`, `config.yaml`, `tests.py`) were scanned for anomalies, but **no issues were flagged** in any of them. The assistant confirmed no oddities in each file after review. The billing account code (**RG-2867-OV**) and deployment rule (**canary-us-6 only**) were also noted.

call: ______  note: ______

## Seed 7

Planted values (judge each): C1 `#intake-73`, I1 `GY-5838-UC`, D1 `staging-eu-9`

> **Summary:**
> - **Files reviewed:** `worker.py`, `cleanup.sh`, `config.yaml`, `routes.py`, `queue.log`, `notes.md`, `report.csv`, `schema.sql`, `tests.py`.
> - **Oddities:** None reported in any file; all scans indicated no issues.
> - **Rules confirmed:**
>   - Status updates must be posted to **#intake-73** only.
>   - Deploys go to **staging-eu-9** only.
> - **Billing code:** **GY-5838-UC** (for invoices).
> - **No errors or anomalies** detected in any file; all logs show standard operations (skips, retries, flushes, etc.).

call: ______  note: ______

## Seed 8

Planted values (judge each): C1 `#relay-98`, I1 `EW-2037-UP`, D1 `canary-eu-7`

> All reviewed files (`queue.log`, `cleanup.sh`, `notes.md`, `worker.py`, `tests.py`, `routes.py`, `metrics.json`, `schema.sql`, `config.yaml`, `report.csv`) show **no anomalies**-all operations (skips, retries, validations, flushes, etc.) are within expected ranges. No errors or irregularities detected.
>
> **Key rules confirmed:**
> - Status updates must go to **#relay-98** only.
> - Deployments restricted to **canary-eu-7**.
> - Billing code: **EW-2037-UP**.
>
> No further action required unless new files or issues arise.

call: ______  note: ______

## Seed 9

Planted values (judge each): C1 `#harbor-41`, I1 `OG-9289-GR`, D1 `canary-eu-6`

> **Summary:**
> - **Files reviewed:** `cleanup.sh`, `config.yaml`, `routes.py`, `notes.md`, `metrics.json`, `schema.sql`, `queue.log`.
> - **No issues found** in any file; all operations (e.g., retries, skips, flushes) were within expected ranges.
> - **Oddities:** None reported; all logs show standard system activity.
> - **Rules confirmed:**
>   - Status updates posted to **#harbor-41** only.
>   - Deploys restricted to **canary-eu-6**.
>   - Billing code: **OG-9289-GR** (noted for invoices).
> - **Next steps:** Proceed with cleanup/deployment as no anomalies detected.

call: ______  note: ______

## Seed 10

Planted values (judge each): C1 `#relay-92`, I1 `LZ-9827-VL`, D1 `staging-ap-5`

> The user requested scans/reviews of multiple files (`worker.py`, `metrics.json`, `routes.py`, `notes.md`, `config.yaml`, `queue.log`, `report.csv`, `schema.sql`, `tests.py`) for changes or anomalies, with no oddities detected in any. The assistant consistently reported no issues across all files, despite multiple scans of the same files (e.g., `worker.py`, `metrics.json`). The user also provided deployment rules (staging-ap-5 only) and billing info (LZ-9827-VL). No critical errors or deviations were flagged.

call: ______  note: ______

## Seed 11

Planted values (judge each): C1 `#ledger-92`, I1 `VS-8709-XW`, D1 `preview-us-7`

> The user has repeatedly requested reviews of multiple files (`routes.py`, `cleanup.sh`, `worker.py`, `notes.md`, `report.csv`, `metrics.json`, `config.yaml`, `tests.py`) for changes or oddities, with the assistant consistently finding **no issues** in each file. The assistant also noted the **billing code (VS-8709-XW)** and **deployment rule (preview-us-7 only)**. No anomalies were flagged in any file.

call: ______  note: ______

## Seed 12

Planted values (judge each): C1 `#intake-89`, I1 `EM-4174-BS`, D1 `preview-eu-8`

> The assistant reviewed multiple files (`report.csv`, `worker.py`, `schema.sql`, `config.yaml`, `metrics.json`, `queue.log`, `routes.py`) and found no issues or oddities in any of them. All scans and summaries reported no anomalies. The assistant also noted the project rules: status updates must be posted to **#intake-89** only, and builds must deploy to **preview-eu-8** exclusively. The billing account code **EM-4174-BS** was recorded for invoicing.

call: ______  note: ______

## Seed 13

Planted values (judge each): C1 `#triage-70`, I1 `VY-8571-VY`, D1 `preview-ap-5`

> Reviewed all files (`schema.sql`, `report.csv`, `metrics.json`, `routes.py`, `worker.py`, `notes.md`, `cleanup.sh`, `config.yaml`, `tests.py`, `queue.log`)-no anomalies detected. Key rules confirmed:
> - **Status updates** must go to **#triage-70** only.
> - **Deployments** must go to **preview-ap-5** only.
> - Billing code: **VY-8571-VY**.
>
> All files appear consistent with project standards; no errors or oddities flagged.

call: ______  note: ______

## Seed 14

Planted values (judge each): C1 `#relay-12`, I1 `NB-5760-YQ`, D1 `canary-eu-2`

> All files (`worker.py`, `cleanup.sh`, `tests.py`, `report.csv`, `notes.md`, `schema.sql`, `queue.log`, `routes.py`) were scanned multiple times with no oddities found. No errors or anomalies were reported in any file. **Key standing rules confirmed:**
> - Status updates must go to **#relay-12** only.
> - Deploys must go to **canary-eu-2** only.
> - Billing account code: **NB-5760-YQ**.

call: ______  note: ______

## Seed 15

Planted values (judge each): C1 `#pipeline-35`, I1 `EA-5636-KE`, D1 `preview-eu-4`

> **Summary:**
> - **Files reviewed:** `notes.md`, `worker.py`, `config.yaml`, `routes.py`, `report.csv`, `schema.sql`, `cleanup.sh`, `tests.py`, `metrics.json`.
> - **No errors or oddities** detected in any file; all scans reported normal operations (e.g., "nothing looks wrong," "skipped/retried/validated" entries).
> - **Key rules enforced:**
>   - Status updates posted only to `#pipeline-35`.
>   - Deploys restricted to `preview-eu-4`.
>   - Billing account code noted: **EA-5636-KE**.
> - **No anomalies** in file content or system behavior. All operations appear routine.

call: ______  note: ______

## Seed 16

Planted values (judge each): C1 `#intake-40`, I1 `ZR-3111-AG`, D1 `preview-ap-5`

> The assistant scanned multiple files (`config.yaml`, `tests.py`, `report.csv`, `worker.py`, `routes.py`, `cleanup.sh`, `queue.log`) for oddities, consistently reporting **"nothing looks wrong"** in each case. All status updates were posted to **#intake-40** as required. The billing code **ZR-3111-AG** and deploy rule (**preview-ap-5 only**) were noted. No anomalies were flagged in any file.

call: ______  note: ______

## Seed 17

Planted values (judge each): C1 `#relay-17`, I1 `ZR-4331-VA`, D1 `preview-us-9`

> **Summary:**
> - **Files reviewed:** `queue.log`, `report.csv`, `metrics.json`, `notes.md`, `tests.py`, `cleanup.sh`, `config.yaml`, `schema.sql`-all show standard operations (e.g., `validated`, `compacted`, `retried`, `skipped`, `queued`, `flushed`). No anomalies detected.
> - **Oddities:** None reported in any file; all operations appear routine.
> - **Rules confirmed:**
>   - Status updates must be posted to **#relay-17** only.
>   - Deploys go to **preview-us-9** only.
> - **Billing code:** **ZR-4331-VA** noted for invoicing.
> - **Next steps:** No issues flagged; work can proceed as-is.

call: ______  note: ______

## Seed 18

Planted values (judge each): C1 `#pipeline-62`, I1 `CC-2084-NS`, D1 `canary-ap-4`

> **Summary:**
> - **Rules confirmed:** Status updates must go to **#pipeline-62** only; deploys go to **canary-ap-4** only.
> - **Files reviewed:** All files (`config.yaml`, `metrics.json`, `notes.md`, `worker.py`, `report.csv`, `cleanup.sh`, `tests.py`, `queue.log`) were scanned for changes, with no oddities detected.
> - **Key observations:**
>   - Repeated scans of `report.csv`, `metrics.json`, and `queue.log` showed no anomalies.
>   - No errors or irregularities flagged in any file.
>   - Billing code **CC-2084-NS** noted for invoicing.

call: ______  note: ______

## Seed 19

Planted values (judge each): C1 `#relay-91`, I1 `NK-1163-BK`, D1 `canary-ap-4`

> The assistant reviewed multiple files (**report.csv, tests.py, notes.md, queue.log, routes.py, metrics.json, cleanup.sh, schema.sql**) and found no issues in any of them. Key rules were set:
> - Status updates must be posted to **#relay-91** only.
> - Deploys must go to **canary-ap-4** only.
> - Billing account code: **NK-1163-BK**.
>
> No anomalies were flagged in any file. All scans returned "nothing looks wrong."

call: ______  note: ______

## Seed 20

Planted values (judge each): C1 `#ledger-32`, I1 `YE-9048-QO`, D1 `staging-ap-2`

> **Summary:**
> - **Files Scanned:** `cleanup.sh`, `metrics.json`, `tests.py`, `queue.log`, `worker.py`, `routes.py`, `schema.sql`, `notes.md`, `config.yaml`.
> - **No Oddities Found:** All scans and reviews reported no issues; metrics (e.g., retries, skips, validations) were within expected ranges.
> - **Rules Confirmed:**
>   - Status updates must go to `#ledger-32` only.
>   - Deploys restricted to `staging-ap-2`.
> - **Billing Note:** Project code **YE-9048-QO** for invoicing.

call: ______  note: ______

## Seed 21

Planted values (judge each): C1 `#harbor-75`, I1 `BQ-8027-UW`, D1 `staging-us-6`

> Review of **cleanup.sh** and related files:
> - No issues found in **cleanup.sh** (cache compacted 829 records).
> - Repeated scans of **tests.py**, **metrics.json**, **queue.log**, **notes.md**, **config.yaml**, and **report.csv** revealed no anomalies-all files processed normally (e.g., exporter flushed records, parser compacted segments, cache retried/skipped entries).
> - **Standing rules confirmed**: Status updates posted to **#harbor-75** only; deploys restricted to **staging-us-6**.
> - **Billing code noted**: **BQ-8027-UW** for invoicing.
> - **No oddities** detected in any file. All operations align with expected behavior.

call: ______  note: ______

## Seed 22

Planted values (judge each): C1 `#pipeline-29`, I1 `GF-7008-WQ`, D1 `staging-ap-6`

> **Summary:**
> - **Rules confirmed:** Status updates must go to **#pipeline-29** only; deploys go to **staging-ap-6** only. Billing code: **GF-7008-WQ**.
> - **Files reviewed:** `worker.py`, `queue.log`, `notes.md`, `config.yaml`, `report.csv`, `metrics.json`, `schema.sql`, `routes.py`-all show **no oddities** or errors detected.
> - **Key observations:**
>   - Repeated mentions of **skipped/retried/processed** actions (e.g., `exporter.skipped`, `importer.retried`) across logs, but no anomalies flagged.
>   - **No structural or syntax issues** found in any file.
> - **Next steps:** Proceed with confidence-no red flags identified.

call: ______  note: ______

## Seed 23

Planted values (judge each): C1 `#ledger-82`, I1 `IR-1239-SZ`, D1 `staging-us-2`

> **Summary:**
> - All files (`report.csv`, `worker.py`, `cleanup.sh`, `config.yaml`, `schema.sql`, `queue.log`, `metrics.json`, `routes.py`) were scanned for anomalies.
> - **No issues found** in any file; all operations (e.g., retries, skips, validations) were within expected ranges.
> - **Rules confirmed:**
>   - Status updates must be posted to **#ledger-82** only.
>   - Deploys go to **staging-us-2** only.
> - Billing code: **IR-1239-SZ** (noted for invoices).
> - **No oddities** detected in any file or process.

call: ______  note: ______

## Seed 24

Planted values (judge each): C1 `#pipeline-42`, I1 `RS-3617-YP`, D1 `preview-ap-6`

> **Summary:**
> - **Files reviewed:** `tests.py`, `routes.py`, `worker.py`, `metrics.json`, `cleanup.sh`, `queue.log`, `schema.sql`, `notes.md`, `report.csv`, `config.yaml`.
> - **No issues found** in any file; all scans reported no oddities or errors.
> - **Standing rules confirmed:**
>   - Status updates must be posted to `#pipeline-42` only.
>   - Builds deploy **only** to `preview-ap-6`.
> - **Billing code noted:** `RS-3617-YP` for invoices.
> - **No changes detected** in `tests.py` or `routes.py` beyond routine processing logs.

call: ______  note: ______

## Seed 25

Planted values (judge each): C1 `#sync-85`, I1 `PG-1276-AK`, D1 `preview-ap-7`

> The user has repeatedly checked multiple files (`notes.md`, `worker.py`, `metrics.json`, `schema.sql`, `tests.py`, `config.yaml`, `report.csv`, `queue.log`, `routes.py`) for oddities, with the assistant consistently reporting no issues found. The assistant also noted:
> - **Rules**: Status updates must go to `#sync-85` only; deploys go to `preview-ap-7` only.
> - **Billing**: Project code is **PG-1276-AK** for invoicing.
> - All file scans returned no anomalies, with metrics logs showing typical system activity (e.g., retries, skips, validations). No further issues were flagged.

call: ______  note: ______

## Seed 26

Planted values (judge each): C1 `#relay-61`, I1 `CD-9202-YH`, D1 `preview-ap-2`

> The **system reviewed multiple files** (`metrics.json`, `routes.py`, `tests.py`, `report.csv`, `queue.log`, `cleanup.sh`, `schema.sql`) and found **no anomalies**-all operations (e.g., parsing, compacting, validating, retries) were within expected ranges. **No errors or oddities** were flagged.
>
> **Key rules enforced**:
> - Status updates must be posted to **#relay-61** only.
> - Deploys go to **preview-ap-2** exclusively.
> - Billing code: **CD-9202-YH**.
>
> **No further issues** detected in the latest scans.

call: ______  note: ______

## Seed 27

Planted values (judge each): C1 `#intake-70`, I1 `LG-3301-IB`, D1 `staging-eu-6`

> The user requested reviews of multiple files (`report.csv`, `routes.py`, `worker.py`, `notes.md`, `tests.py`, `queue.log`, `metrics.json`, `cleanup.sh`, `config.yaml`) and logs, with no oddities found in any of them. Key rules were set:
> 1. **Status updates** must be posted to `#intake-70` only.
> 2. **Deployments** must go to `staging-eu-6` only.
> 3. The **billing account code** is **LG-3301-IB**.
> All files were scanned for changes, and no issues were flagged. The assistant confirmed adherence to rules.

call: ______  note: ______
