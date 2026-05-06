# LTE Methodology — 4G RAN Optimization Trials

This file is the LTE counterpart to `references/nr/methodology_nr.md`. It sits alongside
`references/methodology.md` (the shared base) and documents LTE-specific confirmations,
extensions, and additions.

Read `references/methodology.md` first. That file covers sigma math, verdict mapping,
near-zero variance handling, chart sigma normalisation, H0 (Band Stratification Not
Applicable), and multi-phase trials — all of which apply to LTE exactly as written.
This file covers what is LTE-specific or has been extended beyond the base.

---

## Confirmation 1: Band Stratification applies fully to LTE

The band stratification principle in `methodology.md` was derived from LTE practice and
applies without modification:

- **Feature Bands** — EARFCNs where the parameter under test was changed
- **Unaffected Bands** — EARFCNs present in the cluster where the parameter was NOT changed

Every KPI table in the Statistical Analysis Excel and every KPI section in the Word memo
must present Feature Band and Unaffected Band results separately. This is not optional.

**MNO EARFCN defaults** (confirm against cluster before use):
See `references/lte/carrier_allocation.md` for the full EARFCN→band mapping.
Common bands: B800 (EARFCN 6400), B900 (EARFCN 3050), B1800 (EARFCN 1300),
B2100 (EARFCN 525), B2300_F1, B2300_F2, B700.

Do not assume the default mapping applies to every cluster — confirm with the user or
the parameter change log before assigning Feature vs Unaffected roles.

### When Band Stratification is Not Applicable (H0 — LTE specific)

Some LTE parameter changes affect ALL FDD bands in the cluster simultaneously. When this
occurs, TDD carriers (e.g. B2300) are present but are NOT a valid control group — FDD and
TDD differ fundamentally in scheduling, interference, and load patterns.

**Procedure when H0 applies to LTE:**
1. State in Section 4.3: "Band Stratification Not Applicable — parameter applied to all FDD
   bands; TDD carriers excluded as control due to duplex-mode incomparability."
2. Fall back to baseline vs trial comparison on Feature bands only.
3. Check that the baseline trend is flat — if it shows a pre-existing improvement trend,
   the trial improvement may be its continuation, not the feature's effect.
4. Reference an external cluster if available.
5. Apply verdict calibration from `methodology.md` Section "H0: Band Stratification Not
   Applicable" — default PASS WITH CONDITIONS; upgrade to PASS with external evidence only.

---

## Confirmation 2: H-Hypothesis Framework applies fully to LTE

The H-hypothesis framework in `methodology.md` was built for LTE and applies as written
when a valid unaffected band group exists.

| Hypothesis | Pattern | Conclusion |
|---|---|---|
| H1 — Feature-induced | Feature bands degrade, Unaffected bands stable | Feature caused the degradation |
| H2 — Concurrent network trend | Both band groups degrade similarly | External event coincident with trial |
| H3 — RC-specific SW interaction | Only one RC's unaffected bands degrade | SW version issue, not the feature |
| H0 — No valid control group | All same-technology bands affected (see above) | Baseline-only comparison; caveat verdict |

Apply this framework in Section 4.3 (Retainability) of every LTE trial memo. State which
hypothesis the data supports, with the sigma values as evidence. Do not assert H1 if
the data pattern matches H2.

---

## Confirmation 3: QCI Stratification applies to LTE

Report QCI1 (VoLTE) and QCI8 (default bearer / mobile broadband) separately when data
is available. Traffic-weighted averages across QCIs can obscure the dominant bearer's
behaviour. See `methodology.md` for full guidance.

---

## Confirmation 4: Two-RC Trial Structure — RC3 and RC4 are Regional Areas

**Important**: RC3 and RC4 are **regional cluster areas**, not two separate software releases
running simultaneously in the same cluster.

- **RC3** typically covers Dense Urban environments (city centres, high-rise areas)
- **RC4** typically covers Suburban / Rural environments (lower-density areas)

The software release running in RC3 and RC4 **may be the same or different** — confirm
with the trial plan and Nokia export metadata before analysis. Do not assume they differ.

**Why this matters for analysis:**
- Traffic load, interference profiles, and baseline KPI levels differ systematically between
  Dense Urban and Suburban/Rural areas. Comparing RC3 and RC4 absolute KPI values directly
  is often not meaningful.
- What IS meaningful: comparing the *delta* (trial − baseline) within each RC independently,
  then checking whether both RCs show the same direction of change.
- If SW releases differ between RC3 and RC4, a divergent result may indicate SW-version
  behaviour (H3) rather than a feature effect. Always note SW versions in the memo.

**Analysis rules:**
- Analyse each RC (regional area) independently first
- RC comparisons require similar baseline traffic load (check PRB utilisation; >10 pp
  difference is a caveat requiring documentation)
- Divergent RC results: state the divergence and whether it maps to the geographic
  environment difference or to an SW version difference
- Do not force a unified conclusion when results diverge significantly

---

## Extension 1: Feature Causal Chain — KPI_Trajectories Sheet

### Principle

The `KPI_Trajectories` sheet in the LTE Statistical Analysis Excel must not be a generic
list of high-sigma KPIs. It should reflect the **feature's causal chain** derived from the
Nokia feature document (DN PDF).

> **Note on naming**: The sheet was previously called `Period_Trajectories`. It is now
> standardised to `KPI_Trajectories` across both LTE and NR to maintain a consistent naming
> convention. The chart type remains bar charts (Baseline / Trial / Post-RB) for LTE —
> different from NR's daily line charts, but the sheet name is now unified.

The four-category classification used for NR applies to LTE:

| Category | Definition | Expected direction |
|---|---|---|
| Primary mechanism indicators | KPIs directly reflecting the feature's operation | Must move in designed direction |
| Expected outcome KPIs | KPIs that change as a consequence (may be slightly negative but bounded) | Per spec |
| Watchdog KPIs | KPIs that must NOT degrade — if they do, the feature is causing harm | Must remain ≤ 1σ |
| Traffic context | KPIs needed to detect confounders | Must be stable |

### LTE-specific differences from NR

**Band stratification in trajectories:** Unlike NR (carrier lines only), LTE trajectory
charts should show Feature Band aggregate and Unaffected Band aggregate as two separate
lines per chart (when stratification applies). This allows the reader to see immediately
whether a KPI movement is confined to Feature bands (feature effect) or affects both band
groups (concurrent trend).

Recommended line style:
- Feature Bands aggregate — solid line, colour per RC (RC3=blue, RC4=orange)
- Unaffected Bands aggregate — dashed line, same colour family

### LTE energy / supplementary KPI file

The primary Nokia system program export contains all core KPIs including energy metrics
(DRX Sleep Ratio, PSM Ratio, ReducedTX). For most LTE trials this is the single data source.

However, some features — particularly energy-focused features or features that interact
with specific Nokia counters — may have **supplementary KPI exports** provided separately
(e.g. a dedicated energy or power counter file). When such a file is available:
- Include it in the trial intake form (Section 5: Data Files → RC1/RC2 Energy fields)
- Merge its relevant columns into the analysis where they complement the main export
- Document its source in the memo and flag any KPIs sourced from the supplementary file

Do not assume a supplementary file exists unless the trial plan or trial coordinator
confirms it. When absent, rely on the main Nokia system program export only.

### Procedure — dynamic feature_context.json approach

`build_stats_report_template.py` reads `feature_context.json` from its own directory at
startup via `load_feature_context()`. **Claude generates this file from the Nokia DN PDF
during Step 1a of the skill pipeline.** No manual editing of the script is needed.

If `feature_context.json` is absent, the script falls back to a hardcoded default
`TRAJ_KPIS` list (reference trial). This fallback is for script development and
re-runs of the same trial only — always provide a trial-specific JSON for a new trial.

1. Read the Nokia feature document (mandatory pre-flight input).
2. Identify the mechanism: what does the feature change at the radio/scheduling level?
3. Classify KPIs into the four categories above.
4. Map each to a KPI name as it appears in `RC3_FEAT` / `RC4_FEAT` — these are the
   pre-aggregated statistic rows, not raw data column names.
5. Verify each name exists in the actual data arrays before finalising.
6. Generate `feature_context.json` using the LTE template (`feature_context_template.json`
   in `scripts/lte/`) and save it in the script directory.

**This file must be re-derived for every trial from its feature document.** The pre-built
feature_context_template.json is a starting point for
DRX/PSM-class features only.

### LTE feature_context.json format

```json
{
  "trial_id": "CBXXXXXX",
  "rc3_label": "RC3",
  "rc4_label": "RC4",
  "feature_name": "Feature name from Nokia DN",
  "feature_doc": "DNXXXXXXXXX",
  "mechanism_summary": "One-sentence mechanism description.",
  "t1_kpis": [
    {"col": "PSM Ratio",          "unit": "(%)", "higher_bad": false, "category": "mechanism"},
    {"col": "DRX Sleep Ratio",    "unit": "(%)", "higher_bad": false, "category": "mechanism"},
    {"col": "Avg Latency DL",     "unit": "ms",  "higher_bad": true,  "category": "outcome"},
    {"col": "ERAB Retain. Fail",  "unit": "(%)", "higher_bad": true,  "category": "watchdog"},
    {"col": "UL rBLER",           "unit": "(%)", "higher_bad": true,  "category": "watchdog"}