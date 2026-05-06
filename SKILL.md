---
name: ran-trial-production
description: >
  End-to-end production pipeline for RAN optimization trial analysis. Multi-RAT:
  4G LTE (fully implemented) and 5G NR NSA/EN-DC (Phase 3 — first release). Use
  whenever the user provides KPI statistics from a Nokia RAN trial — whether as
  numbers in a message, a filled intake template, or raw exported data — and wants
  to produce the full deliverable set: KPI trend charts (Excel), statistical
  analysis charts (Excel), and a formal technical memo (Word .docx). Also trigger
  when the user says "generate the trial report", "create the KPI graphs",
  "build the stats Excel", or provides a trial_intake.md template with data
  filled in. Complements ran-trial-analysis (which focuses on the analytical
  verdict) by handling the production artifacts.
---

# RAN Trial Production Pipeline

You are producing the full deliverable set for a RAN optimization trial. This skill
supports two RATs: 4G LTE (mature) and 5G NR NSA/EN-DC (first release — Phase 3).
Regardless of RAT, the skill covers the generation of three artifacts from structured
KPI data:

1. **KPI Charts Excel** (`<TRIAL_ID>_<RAT>_KPI_Grouped.xlsx`) — per-KPI trend charts
   grouped by category, showing Baseline / Trial / Post-RB time series
2. **Statistical Analysis Excel** (`<TRIAL_ID>_<RAT>_Statistical_Analysis.xlsx`) —
   delta%, sigma significance matrix, sigma ranking, per-carrier breakdowns,
   feature-context causal-chain KPI trajectories
3. **Technical Memo** (`<TRIAL_ID>_<RAT>_Trial_Analysis.docx`) — formal Word document
   with executive summary, carrier-stratified KPI analysis, confounding factor
   assessment, and verdict

Read `references/methodology.md` for RAT-agnostic principles. For NR trials, also read
`references/nr/methodology_nr.md` for NR-specific departures (no H1/H2/H3 framework,
carrier-only stratification, ES data separate source).

---

## Step 0: Select RAT (Radio Access Technology)

Before any data work, establish which technology this trial is for. The skill dispatches
to RAT-specific scripts and references:

| RAT        | Scripts path    | References path  | Status                |
|------------|-----------------|------------------|-----------------------|
| LTE (4G)   | `scripts/lte/`  | `references/lte/`| Fully implemented     |
| NR (5G NSA)| `scripts/nr/`   | `references/nr/` | Phase 3 first release |
| NR (5G SA) | —               | —                | Not planned           |

**If the trial is LTE**: proceed to Step 1 using `scripts/lte/` and `references/lte/`
paths referenced throughout.

**If the trial is NR (NSA)**: proceed to Step 1 using `scripts/nr/` and `references/nr/`.
Note these NR-specific differences before you begin:
- Carrier key is `NRARFCN` (not `EARFCN`)
- Carrier-only stratification — **no** Feature/Unaffected band split
- H1/H2/H3 hypothesis framework does **not** apply for NR; see `references/nr/methodology_nr.md`
- ES (energy saving) data is a **second** data source (cluster-level only, no per-carrier)
- Verdict default for a clean NR PASS is **PASS WITH CONDITIONS** unless an external
  control has been reviewed (see methodology_nr.md)

**If the trial is NR (SA)**: not supported. Stop and tell the user.

---

## Step 1: Gather Inputs

### ⛔ MANDATORY PRE-FLIGHT CHECK — HARD STOP IF ANY ITEM IS MISSING

Before writing any code, creating any files, or extracting statistics, verify that ALL of
the following have been explicitly provided by the user. If anything is missing, output the
block below and stop. Do NOT proceed with assumptions, inferences, or best guesses.

**Five required inputs — all must come from the user or an attached document:**

| # | Required input | Valid sources | NOT valid sources |
|---|---|---|---|
| 1 | **Feature name and functional description** — what the feature actually does | User statement, Nokia feature spec, trial plan | Trial ID number, folder name, file path components |
| 2 | **Parameter changed** — exact parameter name, value before, value after | User statement, trial plan, parameter change log | Inference from KPI behaviour or feature category |
| 3 | **Feature bands** — which EARFCNs / NRARFCNs / bands had the parameter changed | User statement, parameter change log | Template defaults, prior trial conventions, methodology examples |
| 4 | **Period dates** — baseline start/end, trial start/end, post-RB start/end (YYYY-MM-DD) | User statement, trial plan, energy sheet with labels the user has confirmed | Energy sheet from a *previous* pipeline run; inferred from file dates |
| 5 | **Unaffected bands** (LTE only) — bands present in cluster where parameter was NOT changed | User statement or parameter change log | Residual after feature bands are assigned without explicit confirmation |

**Additionally for NR trials — also required at pre-flight:**

| # | Required input | Purpose |
|---|---|---|
| 6 | **Nokia feature document** (DN number / PDF) | Read to extract causal chain for KPI_Trajectories (Step 4a). If not attached, ask the user to provide it before proceeding. |

**If any of items 1–5 is missing (or item 6 for NR), output this block and stop:**

```
⛔ MISSING REQUIRED INPUTS — pipeline cannot proceed

The following information must be provided before any analysis or file generation begins.
Please supply each missing item explicitly:

[ ] 1. Feature description: What does this feature do? What is the exact parameter name,
        old value, and new value?
[ ] 2. Feature bands: Which bands/EARFCNs/NRARFCNs had the parameter changed?
[ ] 3. Unaffected bands (LTE): Which bands are present in the cluster but were NOT changed?
[ ] 4. Trial periods: Baseline start–end / Trial start–end / Post-RB start–end (YYYY-MM-DD)?
[ ] 5. (NR only) Nokia feature document (DN number or attached PDF)?

Note: the trial ID, folder name, and file names are identifiers only — they do not
establish the feature description or parameter values. These must be provided explicitly.
```

---

### Three intake paths (in order of preference)

**PATH 1 — Interactive HTML Form (recommended for both LTE and NR):**
Copy `references/trial_intake_form.html` to the user's workspace folder and present
it. The user opens it in their browser and fills in all sections:
- Trial metadata, SW versions, date ranges; **technology selector (LTE / NR)** adapts the form
- LTE: carrier allocation table (MNO defaults, fully editable) + band chip toggle
- NR: NR carrier list (NRARFCN, SCS, Feature vs Unaffected) + H0 flag if all carriers activated
- Multi-phase toggle: adds a phase table (label, start, end, changes) for sequential parameter trials
- Data file paths (LTE: RC1/RC2 KPI + optional energy; NR: RC1/RC2 NR export + ES cluster)
- Feature context and expected impacts; feature doc mandatory for NR
- Confounding events; output preferences and preliminary verdict

When the user clicks "Mark Ready for Processing" and tells Claude to proceed:
1. Open the form in a browser tab using browser tools
2. Read the form state: `window.__TRIAL_INTAKE__` (exposed as a global JS object)
3. This returns a complete JSON config with all fields structured for downstream scripts
4. Extract the `tef_earfcn_map` from the form data to configure `extract_stats.py`
5. Proceed to Step 2

```javascript
// Claude reads the form via javascript_tool:
JSON.stringify(window.__TRIAL_INTAKE__)
```

As a backup, the form also provides a "Download JSON" button that saves the form state
as `trial_intake.json` — use this if the in-browser JS global read fails, by reading
the saved file from the workspace.

**NR is fully supported in the shared form** (`references/trial_intake_form.html`).
The form adapts dynamically: selecting "5G NR" shows the NR carrier table (NRARFCN, SCS,
Feature vs Unaffected, H0 flag) and hides the LTE EARFCN chip-toggle section.
The LTE-specific copy at `references/lte/trial_intake_form.html` is a legacy artefact
— always use the shared form in `references/` for new trials.

**PATH 2 — Raw Nokia KPI export files + conversational intake:**
The user provides the Nokia KPI engine Excel export(s) — one per RC/SW version.
Claude runs `scripts/lte/extract_stats.py` (LTE) or `scripts/nr/extract_stats.py` (NR)
to compute all KPI statistics automatically.
The user supplies trial metadata conversationally or via `references/trial_intake_template.md`.

Run extraction (LTE):
```bash
python3 scripts/lte/extract_stats.py \
    --rc1-file /path/to/RC3_export.xlsx \
    --rc2-file /path/to/RC4_export.xlsx \
    --baseline-start YYYY-MM-DD --baseline-end YYYY-MM-DD \
    --trial-start YYYY-MM-DD --trial-end YYYY-MM-DD \
    --post-rb-start YYYY-MM-DD --post-rb-end YYYY-MM-DD \
    --feature-bands B800,B900,B1800,B2100 \
    --unaffected-bands B700,B2300_F1,B2300_F2 \
    --rc1-label RC3 --rc2-label RC4 \
    --trial-id TRIAL_ID --out-dir /tmp/TRIAL_ID
```

Run extraction (NR):
```bash
python3 scripts/nr/extract_stats.py \
    --kpi-file /path/to/5G_System_Program_export.xlsx \
    --es-file /path/to/ES_report_per_cluster.xlsx \
    --baseline-start YYYY-MM-DD --baseline-end YYYY-MM-DD \
    --trial-start YYYY-MM-DD --trial-end YYYY-MM-DD \
    --trial-id TRIAL_ID --out-dir /tmp/TRIAL_ID
```

The scripts print Python data arrays and save a CSV summary. Review the CSV before
building the report — verify the numbers look reasonable before accepting them.

**PATH 3 — Manual statistics (fallback if no raw files):**
The user fills in Sections 5-manual, 6-manual, 7-manual of the intake template.
This requires ~40 values per RC, entered manually. Only use this path when raw exports
are genuinely unavailable.

### Required inputs (all paths)

Regardless of intake path, you must have — at minimum — all items from the pre-flight
check above, plus:
- Carrier EARFCN→band mapping (see `references/lte/carrier_allocation.md` for MNO LTE
  defaults; see `references/nr/carrier_allocation.md` for MNO NR defaults)
- Confounding events known to the user (outages, SW upgrades, hardware changes during trial
  window) — these cannot be derived from KPI data alone

**The feature name appearing in all three deliverables must come from items 1 and 2 of the
pre-flight check — never from folder path, file name, or trial ID.**

Do not proceed with incomplete inputs. If the EARFCN/NRARFCN map in extract_stats.py does
not match the cluster, ask the user for the mapping before running.

---

## Step 1a: Extract Feature Causal Chain (NR only — feeds Step 4a)

**This step is mandatory for NR trials and must be completed before Step 4.**

Read the Nokia feature document provided in pre-flight item 6. Extract:

1. **Mechanism** — exactly what the feature changes at a radio/scheduling/hardware level
   (e.g. "consolidates DL PDSCH slots to create PA sleep gaps", "mutes MIMO layers when
   traffic is low", "adjusts beamforming weights based on UE geometry")

2. **Expected primary indicators** — KPIs that should improve if the feature works
   (e.g. ReducedTX Ratio ↑, energy consumption ↓)

3. **Expected mechanism KPIs** — KPIs that will change as a direct consequence of the
   mechanism, even if that change is neutral or slightly negative
   (e.g. PDSCH Slot Usage ↓ for µDTX, DL Rank ↓ for MIMO muting)

4. **Watchdog KPIs** — KPIs that must NOT degrade beyond threshold; if they do, the
   feature is causing harm
   (e.g. PDCCH starvation, SgNB abnormal release, accessibility ratios)

5. **Traffic context KPIs** — KPIs needed to interpret the results as a confound check
   (e.g. active UE count, PRB utilisation)

Document findings in this structure before proceeding. This list becomes the content of
`feature_context.json`, which you generate in Step 4a.

**Important distinction — do not confuse feature mechanisms:**
- µDTX / Enhanced DTX (µDTX class): PA-level sleep via DL slot consolidation — NOT MIMO sleep
- MIMO sleep / antenna muting: different feature class with different KPI signatures
- Beamforming / BF weight optimisation: another distinct class

If the feature document is ambiguous, state the ambiguity explicitly and ask the user
to confirm the mechanism before building the causal chain.

---

## Step 2: Set Up Environment

Install xlsxwriter if not present:
```bash
pip install xlsxwriter --break-system-packages --quiet
npm install docx  # for the Word report
```

Create a working directory at `/tmp/<TRIAL_ID>/` for scripts and intermediate files.
Final outputs go to the workspace folder (the user's selected directory).

---

## Step 3: Generate KPI Charts Excel

### LTE variant

Use `scripts/lte/build_kpi_charts_template.py` as your starting point.

1. Replace the `# === DATA INPUT BLOCK ===` section with the actual trial data
2. Update `TRIAL_ID`, `RC_LABELS`, `DATE_RANGES` at the top
3. Replace the time-series data arrays with actual weekly aggregated values from the input
4. Run: `python3 /tmp/<TRIAL_ID>/build_kpi_charts.py`

**Output:** `<TRIAL_ID>_KPI_Grouped.xlsx`

The template produces 54 charts across 22 sheets, grouped by KPI category. Key design rules:
- Baseline period: blue (#2E75B6), Trial period: orange (#ED7D31), Post-RB period: green (#70AD47)
- Each sheet covers one KPI category; each chart covers one carrier/band combination
- Weekly aggregation is standard (resample to 7-day means); daily if < 3 weeks of data
- Use xlsxwriter (NOT openpyxl — openpyxl produces malformed XML for charts)

### NR variant

Use `scripts/nr/build_kpi_charts_nr.py`. Run directly against the raw Nokia export files
(no manual data entry required — the script loads files, filters by NRARFCN, and aggregates):

```bash
# Update MAIN_FILE, ES_FILE, OUT_PATH constants at the top of the script, then:
python3 scripts/nr/build_kpi_charts_nr.py
```

**Expected output:** `<TRIAL_ID>_NR_KPI_Grouped.xlsx`  
**Expected structure:** 24 sheets / 49 charts

Sheet layout:
```
Cover  →  Agg_Data  →  11 × (D_<group> hidden  +  C_<group> charts)
```

Groups (in order): EnergySaving, Latency, Throughput, Accessibility, Retainability,
EN_DC, PDCCH, Mobility, RadioQuality, Traffic, BTS_Energy

Design rules (must match LTE aesthetic):
- Combined chart: line chart (KPI data) + column chart (trial marker bar, red #CC0000, 20% transparency)
- Trial marker column is on secondary Y-axis (0–1 scale, labels hidden via `';;;'` format)
- Date X-axis: `date_axis=True`, 7-day major units, `dd-mmm` format
- Legend: right side, no line markers, line width 1.5
- Chart size: 780 × 380 px
- D-tabs hidden via `ds.hide()` — user accesses via right-click → Unhide
- Phase row shading in D-tabs: yellow `#FFFDE7` = Trial period
- BTS_Energy group uses ES cluster file (no carrier split); single brown `#8B4513` line per chart
- Carrier colours: N28=`#D62728`, N78_F1=`#1F77B4`, N78_F2=`#2CA02C`, N78_F3=`#9467BD`

**Customisation required per trial:**
- `TRIAL_ID`, `RC_LABEL`, `TRIAL_START` at top of script
- `MAIN_FILE` and `ES_FILE` paths
- `MNO_NR_NRARFCN_MAP` — confirm NRARFCN→carrier mapping against the actual cluster
  (see `references/nr/carrier_allocation.md` for MNO defaults)
- KPI group definitions in `META_GROUPS` — add, remove, or rename chart groups if the
  new trial has KPIs not covered by the current groups

Verify the output:
```python
import zipfile, re
with zipfile.ZipFile(path) as z:
    sheets = [n for n in z.namelist() if n.startswith('xl/worksheets/sheet')]
    charts = [n for n in z.namelist() if n.startswith('xl/charts/chart')]
    print(f'Sheets: {len(sheets)}, Charts: {len(charts)}')
# Expected: Sheets=24, Charts=49 (reference count; will differ if KPI groups change)
```

---

## Step 4: Generate Statistical Analysis Excel

### LTE variant

Use `scripts/lte/build_stats_report_template.py` as your starting point.

1. Replace the `# === DATA INPUT BLOCK ===` section with the actual KPI statistics
2. Update `RC3_FEAT` and `RC4_FEAT` arrays (20 KPIs each: name, tier, higher_bad flag,
   baseline, trial, post-rb, sigma)
3. Update `BAND_CMP` dict (5 KPIs × feature vs unaffected × RC3/RC4)
4. Update `PC_RC3` / `PC_RC4` dicts (per-carrier pairs)
5. Run: `python3 /tmp/<TRIAL_ID>/build_stats_report.py`

**Output:** `<TRIAL_ID>_Statistical_Analysis.xlsx`

The template produces 6 sheets:
- `Significance_Matrix` — color-coded KPI table (red ≥3σ, orange ≥2σ, amber ≥1σ, grey <1σ)
- `Sigma_Charts` — horizontal bar chart RC3 vs RC4 sigma values, degradation-positive normalised
- `KPI_Trajectories` — Baseline/Trial/Post-RB grouped column charts for 8 key KPIs
- `Band_Comparison` — feature vs unaffected delta% for 5 watchdog KPIs, 4-series chart
- `Per_Carrier_Detail` — B800/B900/B1800/B2100 values with grouped column charts
- `Significance_Ranking` — all KPIs sorted by max |σ|

**Critical sigma convention:** `chart_sigma = sigma if higher_bad else -sigma`
This normalises all KPIs so positive = degradation in charts, regardless of KPI direction.
Do NOT reverse this: a positive chart sigma must always mean the KPI moved in a bad direction.

### NR variant

Use `scripts/nr/build_stats_report_nr.py`. Run directly against the raw Nokia export
files (script loads, filters, and aggregates internally — paste the extracted NR_RC1_FEAT,
NR_PC_RC1, NR_ES_FEAT arrays into the data block at the top):

```bash
python3 scripts/nr/build_stats_report_nr.py
```

**Expected output:** `<TRIAL_ID>_NR_Statistical_Analysis.xlsx`  
**Expected structure:** 7 sheets / 21 charts

Sheet layout:
```
Overview  →  Significance_Matrix  →  Sigma_Chart  →  Significance_Ranking
→  Per_Carrier_Detail  →  Energy_Saving  →  KPI_Trajectories
```

Sheet descriptions:
- `Overview` — trial metadata, verdict placeholder, data quality notes
- `Significance_Matrix` — 78-row colour-coded sigma table (70 carrier KPIs + 8 ES KPIs)
- `Sigma_Chart` — horizontal bar chart, degradation-positive; red=degradation, green=improvement
- `Significance_Ranking` — all KPIs sorted by |chart_sigma| descending
- `Per_Carrier_Detail` — per-carrier baseline/trial/σ values, colour-coded
- `Energy_Saving` — ES KPI stats table + 7 cluster-level trajectory charts (brown line)
- `KPI_Trajectories` — **feature causal-chain KPI trajectories** (see Step 4a below)

The sigma normalisation convention is identical to LTE:
`chart_sigma = sigma if higher_bad else -sigma` → positive always = degradation.

**Customisation required per trial:**
- `TRIAL_ID`, `RC_LABEL`, `TRIAL_START` at top of script
- `MAIN_FILE`, `ES_FILE`, `OUT_PATH` paths
- `NR_RC1_FEAT`, `NR_ES_FEAT`, `NR_PC_RC1` data arrays (from extract_stats.py output)
- `feature_context.json` in the script directory — generated by Claude per Step 4a (controls KPI_Trajectories)

---

## Step 4a: Generate feature_context.json for KPI Trajectories (both RATs — mandatory)

The `KPI_Trajectories` sheet plots the feature's causal chain as daily time-series charts,
split by carrier (carrier-stratified, from main file) and cluster-level energy (from ES file).
**This must be customised for every trial — it is not generic.**

**Why this matters:** a hardcoded generic KPI list (e.g. "top 5 KPIs by sigma") produces
a sheet that shows statistical outliers but tells no story about what the feature is doing.
The causal-chain approach shows exactly the sequence of effects that should be visible
if the feature is working correctly — making it immediately readable by an RF engineer.

### How it works — dynamic JSON approach

`build_stats_report_nr.py` does **not** contain hardcoded T1_KPIS. Instead, it reads a
`feature_context.json` file from the same directory at runtime via `load_feature_context()`.
**Claude generates this file from the Nokia feature document (DN PDF) during Step 1a.**
No manual editing of the script is required — only the JSON file changes between trials.

If `feature_context.json` is absent, the script prints a warning and skips the
`KPI_Trajectories` sheet entirely (all other sheets are generated normally).

### Procedure

1. Ensure the Nokia DN PDF is attached (Step 1 input item 6).
2. Execute Step 1a to extract the causal chain (four-category classification).
3. Map each KPI to its exact column name from `references/nr/kpi_column_map.md`.
   Verify the column exists in the actual data file — use `python3 -c "import pandas as pd; print(list(pd.read_csv('...').columns))"` if needed.
4. Generate `feature_context.json` using the template below and save it **in the same
   directory as `build_stats_report_nr.py`** before running the script.
5. Run the script. It will log `load_feature_context: loaded N carrier KPIs, M ES KPIs from feature_context.json`.
6. Treat any `[warn] KPI_Trajectories: N KPI(s) not found` as a column name mismatch — fix
   the JSON (not the script) and re-run.

### feature_context.json structure

```json
{
  "trial_id": "CBXXXXXX",
  "rc_label": "RC1",
  "feature_name": "Enhanced µDTX Optimized Scheduler",
  "feature_doc": "DN294077289",
  "mechanism_summary": "Consolidates DL PDSCH slots in time to create PA micro-sleep gaps between bursts; primary saving via PA micro-sleep (ReducedTX Ratio). Expected: PDSCH Slot Usage ↓, MAC Tput DL ↓ (bounded). Watchdogs: PDCCH starvation ↑, SgNB abnormal release ↑.",
  "t1_carrier_kpis": [
    {"col": "exact column name from data",  "label": "Short Label",  "unit": "(%)",   "category": "mechanism"},
    {"col": "exact column name from data",  "label": "Short Label",  "unit": "(Mbps)","category": "outcome"},
    {"col": "exact column name from data",  "label": "Short Label",  "unit": "(%)",   "category": "watchdog"},
    {"col": "exact column name from data",  "label": "Short Label",  "unit": "(—)",   "category": "context"}
  ],
  "t1_es_kpis": [
    {"col": "exact ES column name",         "label": "Short Label",  "unit": "(Wh)"}
  ]
}
```

Valid `category` values: `"mechanism"`, `"outcome"`, `"quality"`, `"watchdog"`, `"context"`.
Order of entries controls chart order — put mechanism KPIs first.

### NR feature_context.json

The pre-built file `feature_context.json` (in `scripts/nr/`) is the
reference. Copy it to the script directory and rename to `feature_context.json`:

```
cp scripts/nr/feature_context.json scripts/nr/feature_context.json
```

Its carrier KPI list (derived from DN294077289):

| Category  | Column name (data file) | Label | Unit |
|-----------|------------------------|-------|------|
| mechanism | Usage ratio of PDSCH data slots over all DL data slots | PDSCH Slot Usage | (%) |
| mechanism | Cell in Reduced TX Power Saving Mode Ratio | ReducedTX Ratio | (%) |
| mechanism | DRX sleep time ratio | DRX Sleep Ratio | (%) |
| outcome   | Average MAC layer user throughput in downlink | Avg MAC Tput DL | (Mbps) |
| quality   | Average wideband CQI 256QAM table | Avg Wideband CQI | (—) |
| quality   | Average rank used in downlink | Avg DL Rank | (—) |
| watchdog  | Average PDCCH CCE starvation ratio in cell | PDCCH Starvation | (%) |
| watchdog  | QoS Flow Drop Ratio _ RAN view | QoS Flow Drop | (%) |
| watchdog  | SgNB triggered abnormal release ratio excluding X2 reset | SgNB Abn Release | (%) |
| context   | Average number of active UEs with data in the buffer for DRBs in DL | Active DL UEs | (—) |

ES KPIs: `[N]ENERGY_CONSUMPTION_IN_BTS` (Total BTS Energy), `[N]RU_ENERGY_CONSUMPTION`
(RU Energy), `[N]ENERGY_CONSUMPTION_IN_RF` (RF Energy).

### For a different NR feature

Generate a new `feature_context.json` from that trial's Nokia DN PDF. The template file
is a reference, not a template to modify in-place. The KPI list for a MIMO enhancement or
beamforming feature will be completely different — do not reuse a prior trial's list.

---

## Step 4a (LTE): Generate feature_context.json for KPI_Trajectories

The LTE stats script (`build_stats_report_template.py`) uses the same dynamic JSON
approach as NR. `load_feature_context()` reads `feature_context.json` from the script
directory at startup. If absent, the script falls back to a hardcoded default TRAJ_KPIS
(example). Always provide a trial-specific JSON for production trials.

### How it works — LTE-specific mechanics

The LTE `KPI_Trajectories` sheet shows **grouped bar charts** (Baseline / Trial /
Post-RB) for the causal-chain KPIs — not daily time-series as in NR. The `col` field
in `feature_context.json` must match the KPI name as it appears in `RC3_FEAT` / `RC4_FEAT`
(the pre-aggregated data rows), not the raw Nokia export column header.

### LTE format differences from NR

| Difference | LTE | NR |
|---|---|---|
| `t1_es_kpis` | Not present in standard LTE (energy KPIs come from main export). Add to `t1_kpis` if a supplementary energy file is provided. | Required for NR (3 energy columns from ES cluster file) |
| `higher_bad` per KPI | Required in JSON (used for bar colour coding) | In kpi_column_map.md separately |
| `col` must match | Name in RC3/RC4_FEAT row | Raw data column header |
| Chart type | Grouped bar (BL/Trial/Post-RB) | Daily time-series line |
| If JSON absent | Falls back to default TRAJ_KPIS | Skips sheet entirely |

### LTE feature_context.json structure

```json
{
  "trial_id": "CBXXXXXX",
  "rc3_label": "RC3",
  "rc4_label": "RC4",
  "feature_name": "Feature name",
  "feature_doc": "DNXXXXXXXXX",
  "mechanism_summary": "One sentence.",
  "t1_kpis": [
    {"col": "PSM Ratio",         "unit": "(%)", "higher_bad": false, "category": "mechanism"},
    {"col": "DRX Sleep Ratio",   "unit": "(%)", "higher_bad": false, "category": "mechanism"},
    {"col": "Avg Latency DL",    "unit": "ms",  "higher_bad": true,  "category": "outcome"},
    {"col": "ERAB Retain. Fail", "unit": "(%)", "higher_bad": true,  "category": "watchdog"},
    {"col": "UL rBLER",          "unit": "(%)", "higher_bad": true,  "category": "watchdog"}
  ]
}
```

### LTE feature_context.json example

`feature_context_template.json` (in `scripts/lte/`) is the starting template for the
allowTrafficConcentration feature (DRX/PSM class). For any other LTE feature, generate
a new file from the Nokia DN PDF. Copy and rename:

```
cp scripts/lte/feature_context_template.json scripts/lte/feature_context.json
```

Then edit to match the new trial's mechanism and KPI names.

### Procedure (LTE)

1. Run Step 1a to extract the causal chain from the Nokia DN PDF.
2. Map each KPI to its exact name in `RC3_FEAT` / `RC4_FEAT` — the name used in the
   data arrays, not the raw export header.
3. Set `higher_bad` correctly for each KPI (true = larger value = worse; false = opposite).
4. Generate `feature_context.json` and save in the script directory.
5. Run the script. Check: `KPI_Trajectories: N feature-context KPIs loaded`.
6. Any KPI not found in the data arrays produces a silent skip (no chart for that KPI).
   Check the output sheet has the expected number of charts.

---

## Step 5: Generate Technical Memo (Word Report)

### LTE variant

Use `scripts/lte/trial_memo_template.js` as your starting point. It uses the `docx` npm library.

1. Replace trial metadata at the top (`TRIAL_ID`, `FEATURE_NAME`, `DATE_RANGES`, `VERDICT`)
2. Fill in the band scope table (Section 2.3)
3. Fill in KPI values in all tables (Sections 4.1–4.4)
4. Update the sigma/delta values in the appendix tables
5. Set the verdict and reasoning in Section 6
6. Run: `node /tmp/<TRIAL_ID>/trial_memo.js`

**Output:** `<TRIAL_ID>_Trial_Analysis.docx`

The document structure (do not change section numbers):
1. Executive Summary
2. Trial Description (2.1 Objective, 2.2 Timeline, 2.3 Band Scope table)
3. Data Quality Assessment
4. KPI Analysis (4.1 Power Saving, 4.2 Latency, 4.3 Retainability, 4.4 Accessibility)
5. Confounding Factor Assessment
6. Verdict and Recommendation
7. Appendix (full KPI tables by RC, per-carrier detail)

**Band stratification — this is mandatory, not optional (LTE):**
Every analysis section must separately report Feature bands and Unaffected bands results.
If a KPI degrades on BOTH feature and unaffected bands, that is confounding evidence.
Apply the H-hypothesis framework (see `references/methodology.md`) for retainability.

### NR variant

Use `scripts/nr/trial_memo_nr.js`. Run:
```bash
cd /tmp/<TRIAL_ID> && npm install docx && node trial_memo_nr.js
```

**Output:** `<TRIAL_ID>_NR_Trial_Analysis.docx`

NSA-adapted document structure:
1. Executive Summary
2. Trial Description (2.1 Objective, 2.2 Timeline, 2.3 **Carrier Scope** table)
3. Data Quality Assessment (must state: "Concurrent network effects cannot be
   distinguished from feature effects using in-cluster data alone")
4. KPI Analysis:
   - 4.1 Energy Saving KPIs
   - 4.2 Latency
   - 4.3 Throughput
   - 4.4 NSA-Specific (SgNB and EPS Fallback)
   - 4.5 Accessibility and Retainability
5. Confounding Factor Assessment
6. Verdict and Recommendation
7. Appendix:
   - 7.1 **BTS-Level Sanity Check** — quantitative per-BTS consistency analysis
   - 7.2 Full KPI table (all carriers)

**Key NR memo rules:**
- No band stratification — carrier-stratified only (N28, N78_F1, N78_F2, N78_F3)
- No H1/H2/H3 framework — Section 3 must state concurrent network effects caveat explicitly
- Default verdict for a clean NR PASS: **PASS WITH CONDITIONS**, unless an external
  control has been reviewed
- Section 7.1 BTS sanity check is mandatory — run before generating the memo and embed
  findings (see Step 5a)

### Step 5a: BTS-Level Sanity Check (NR — mandatory before memo)

Before generating the Word memo, run a per-BTS consistency analysis to verify the
feature behaved uniformly across the cluster. This uses the raw main KPI file (not the
cluster-level aggregate) to check per-BTS behaviour for the primary causal-chain KPIs
identified in Step 1a.

The check answers:
- What fraction of BTSs show the expected PDSCH slot decrease (or equivalent primary
  mechanism KPI change)?
- Are there outlier BTSs (z-score > 2.5) showing anomalous behaviour?
- Is traffic stable across BTSs (confound control)?

Findings from this check populate Section 7.1 of the memo quantitatively:
- N/total BTSs showing expected primary KPI change (% coverage)
- Number of outlier BTSs by KPI
- Z-score threshold used
- Brief interpretation of each outlier pattern

Do NOT write qualitative placeholder text in Section 7.1 — it must contain the actual
numbers from the analysis.

Validate the memo output:
```python
from docx import Document
doc = Document(output_path)
print(f'Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}')
# Expected: ≥ 150 paragraphs, ≥ 11 tables
```

---

## Step 6: Verify and Present

Run all three verification checks:

**KPI Charts Excel:**
```python
import zipfile, re
with zipfile.ZipFile(kpi_path) as z:
    sheets = len([n for n in z.namelist() if n.startswith('xl/worksheets/sheet')])
    charts = len([n for n in z.namelist() if n.startswith('xl/charts/chart')])
print(f'Sheets: {sheets}, Charts: {charts}')
# NR expected: Sheets=24, Charts=49 (reference; adjust if KPI groups changed)
# LTE expected: Sheets=22, Charts=54
```

**Stats Excel:**
```python
with zipfile.ZipFile(stats_path) as z:
    sheets = len([n for n in z.namelist() if n.startswith('xl/worksheets/sheet')])
    charts = len([n for n in z.namelist() if n.startswith('xl/charts/chart')])
print(f'Sheets: {sheets}, Charts: {charts}')
# NR expected: Sheets=7, Charts=21
```

**Word memo:**
```python
from docx import Document
doc = Document(memo_path)
print(f'Paragraphs: {len(doc.paragraphs)}, Tables: {len(doc.tables)}')
# NR expected: ≥ 150 paragraphs, ≥ 11 tables
```

Then present all three files to the user:
```
mcp__cowork__present_files with the three output paths
```

Follow up with a one-paragraph summary: verdict, the one or two sigma findings that drove
it, and whether any watchdog KPIs showed significant movement.

---

## H0: When Band Stratification Cannot Be Applied

When the trial parameter affects ALL same-technology bands in the cluster, document H0:
- **LTE all-FDD scenario**: All FDD EARFCNs changed; TDD (B2300) carriers NOT a valid control
- **NR all-carrier scenario**: Feature activated on all NR cells simultaneously

In both cases:
1. State "Band Stratification Not Applicable" in Section 4.3 of the memo with the reason
2. Rely on baseline-only comparison (trial vs baseline on feature bands)
3. Check baseline trend stability (flat = stronger H1 support)
4. Note if an external reference cluster is available
5. Default verdict: PASS WITH CONDITIONS; upgrade to PASS only with external evidence

See `references/methodology.md` → "H0: Band Stratification Not Applicable" for full rules.

---

## Multi-Phase Trials

When a trial has sequential parameter changes (Phase 1 → Phase 2 → Phase 3):
1. The Nokia export is typically a single file covering the full period — use date ranges to slice
2. Each phase is compared against its immediate predecessor (Ph2 vs Ph1, not Ph2 vs Baseline)
3. KPI charts: add vertical shading at each phase boundary with a legend
4. Statistical Analysis Excel: add one sigma column per phase comparison
5. Technical Memo: one subsection per phase within each KPI section (4.1–4.5)
6. Overall verdict: based on final activated state vs Baseline
7. Trial intake form: use `trial_periods.phases` array (each entry: label, start, end, changes_applied)

---

## Common Pitfalls

- **Using the wrong feature mechanism for KPI_Trajectories:** µDTX (PA micro-sleep via
  slot consolidation), MIMO sleep (spatial layer muting), and beamforming optimisation are
  distinct feature classes with different causal chains and KPI signatures. Always derive
  the KPI list from the actual feature document. Never reuse a prior trial's
  `feature_context.json` without re-deriving it from the new feature's DN.

- **Not providing feature_context.json before running the script:** The script reads
  `feature_context.json` from its own directory at startup. If the file is absent, the
  `KPI_Trajectories` sheet is silently skipped. Generate this file during Step 4a (Claude
  produces it from the Nokia DN PDF) and copy it to the script directory before running.
  The `feature_context_template.json` is a starting
  point for µDTX trials — rename it to `feature_context.json` in the script directory.

- **Near-zero baseline variance exploding sigma:** If baseline std dev ≈ 0 for a KPI (e.g.
  a ratio that was constantly 100% during baseline), sigma becomes meaningless. Document this
  in the legend with: "absolute pp delta is the operative metric." Don't suppress the row —
  just flag it.

- **RC-specific software events masquerading as feature degradation (LTE):** If a KPI
  degrades on only one RC's unaffected bands but not the other, this is H3 — a SW version
  interaction, not a feature effect. Always note SW versions in the memo and check whether
  the divergence tracks the SW version boundary rather than the geographic boundary.

- **RC3 and RC4 are regional cluster areas, not two simultaneous SW releases:**
  RC3 typically covers Dense Urban environments; RC4 covers Suburban/Rural. The SW release
  running in each RC may be the same or different — confirm from the trial plan and Nokia
  export metadata before analysis. Do NOT assume SW releases differ between RCs.
  What IS meaningful to compare: the *delta* (trial − baseline) within each RC independently,
  then checking whether both RCs show the same direction of change.

- **TDD carriers are not a valid H-framework control group (LTE):** When a parameter is
  applied to all FDD bands simultaneously, TDD bands (e.g. B2300) are present in the cluster
  but cannot serve as the "Unaffected" control group — FDD and TDD differ fundamentally in
  scheduling, interference, and load patterns. Declare H0 and fall back to baseline-only
  comparison. See `references/lte/methodology_lte.md` for the full H0 procedure.

- **Treat KPI_Trajectories as causal-chain evidence, not a best-of KPIs list:**
  Select KPIs that reflect the feature's mechanism (primary indicators), expected downstream
  effects (outcome KPIs), must-not-degrade safeguards (watchdog KPIs), and traffic context.
  Never populate this sheet with whichever KPIs happened to have the highest sigma — derive
  the list from the Nokia feature document before running any script.
