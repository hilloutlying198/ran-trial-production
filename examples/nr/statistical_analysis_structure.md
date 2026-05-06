# NR Statistical Analysis Excel — Output Structure Reference

**File:** `CBXXXXXX_<RC>_NR_Statistical_Analysis.xlsx`  
**Script:** `scripts/nr/build_stats_report_nr.py`  
**One file per RC** (e.g. RC1 and RC2 produced separately).

---

## Sheet inventory (9 sheets)

| # | Sheet name | Type | Content |
|---|-----------|------|---------|
| 1 | `Overview` | Metadata | Trial parameters, period dates, methodology notes |
| 2 | `Significance_Matrix` | Analysis | Per-KPI: Baseline / Trial / Post-RB means, Δ%, σ (raw & chart), significance level |
| 3 | `Sigma_Chart` | Chart | Horizontal bar chart: all KPIs ranked by chart-sigma (degradation-positive) |
| 4 | `Significance_Ranking` | Analysis | All KPIs ranked by \|σ\| descending |
| 5 | `Per_Carrier_Detail` | Analysis | Selected T1 KPIs broken down per carrier |
| 6 | `Energy_Saving` | Analysis | ES-specific KPIs with σ analysis + daily trajectory charts |
| 7 | `D_ES_Data` | Data (hidden) | Daily ES KPI time-series feeding Energy_Saving charts |
| 8 | `KPI_Trajectories` | Charts | Feature causal-chain KPI daily time-series, carrier-stratified |
| 9 | `D_KT_Data` | Data (hidden) | Daily KPI time-series feeding KPI_Trajectories charts |

---

## Overview sheet

| Row | Column A (label) | Column B (value) |
|-----|-----------------|-----------------|
| 1 | *(title)* | `CBXXXXXX NR NSA Statistical Analysis — RC1` |
| 2 | `Trial ID:` | `CBXXXXXX` |
| 3 | `RC:` | `RC1` |
| 4 | `Feature:` | `<feature name>` |
| 5 | `Feature doc:` | `<Nokia document number>` |
| 6 | `Technology:` | `NR NSA (EN-DC)` |
| 7 | `Baseline:` | `DD Mon YYYY → DD Mon YYYY` |
| 8 | `Trial:` | `DD Mon YYYY → DD Mon YYYY` |
| 9 | `Post-RB:` | `DD Mon YYYY → DD Mon YYYY` (or `n/a (no rollback)`) |
| 10 | `Carriers:` | `N28, N78_F1, N78_F2, N78_F3` |
| 11 | `Parameters:` | `<parameter>=<value>; ...` |
| 12 | `Mechanism:` | `<brief mechanism description>` |
| 13 | `H0 note:` | Feature activated on ALL NR carriers — no internal control group. |
| 14 | `Concurrent effects:` | Concurrent changes cannot be distinguished from feature effects. |
| 15 | `Sigma convention:` | Degradation-positive: positive sigma = worse |
| 16 | `Colour thresholds:` | ≥3σ = red/green; ≥2σ = orange/teal; ≥1σ = yellow/blue; <1σ = grey |

---

## Significance_Matrix — column layout

| Column | Header | Format | Notes |
|--------|--------|--------|-------|
| A | `KPI` | Text | Short display name; background = tier colour |
| B | `Tier` | Text | T1-ES / T1-Lat / T1-Tput / T2 / T3 / T4-Traffic |
| C | `Baseline` | `#,##0.00` | Mean over baseline window |
| D | `Trial` | `#,##0.00` | Mean over trial window |
| E | `Post-RB` | `#,##0.00` | Mean over post-RB window (or `n/a`) |
| F | `Δ%` | `+0.00;-0.00` | (Trial − Baseline) / Baseline × 100 |
| G | `σ (raw)` | `+0.00;-0.00` | (Trial mean − Baseline mean) / Baseline std dev |
| H | `σ (chart)` | `+0.00;-0.00` | Degradation-positive: flipped for KPIs where lower = worse |
| I | `Sign. level` | Text | `≥3σ` / `≥2σ` / `≥1σ` / `<1σ` / `N/A`; colour-coded |

**Tier colour legend (column A background):**

| Tier | Colour | Meaning |
|------|--------|---------|
| T1-ES | `#E2EFDA` green-tint | Primary energy-saving KPI — expected to move |
| T1-Lat | `#DAEEF3` blue-tint | Primary latency KPI — may be impacted |
| T1-Tput | `#FFF2CC` yellow-tint | Primary throughput KPI — may decrease by design |
| T2 | `#F2F2F2` light grey | Secondary diagnostic KPI |
| T3 | `#FFFFFF` white | Watchdog / service quality KPI — must not degrade |
| T4-Traffic | `#EDE7F6` lavender | Traffic context — not directly attributed to feature |

**Example rows** (values anonymised, ordered by tier):

| KPI | Tier | Baseline | Trial | Post-RB | Δ% | σ (raw) | σ (chart) | Sign. |
|-----|------|----------|-------|---------|-----|---------|-----------|-------|
| ReducedTX Ratio | T1-ES | 0.00 | 0.00 | 0.00 | n/a | n/a | n/a | N/A |
| DRX Sleep Ratio | T1-ES | 50.21 | 50.04 | 50.23 | −0.34% | −0.42 | +0.42 | <1σ |
| PDSCH Slot Usage | T1-ES | 31.19 | 28.13 | 32.97 | −9.80% | −2.17 | +2.17 | ≥2σ 🟠 |
| Avg DL Delay CU-UP | T1-Lat | 30.97 | 30.86 | 32.17 | −0.35% | −0.03 | −0.03 | <1σ |
| Avg MAC Tput DL | T1-Tput | 1.24 | 0.95 | 1.11 | −23.1% | −2.61 | +2.61 | ≥2σ 🟠 |
| Avg CQI 256QAM | T2 | 9.84 | 10.12 | 9.91 | +2.8% | +3.58 | −3.58 | ≥3σ 🟢 |
| NGAP Setup SR | T3 | 99.23 | 98.91 | 99.18 | −0.32% | −4.79 | +4.79 | ≥3σ 🔴 |
| Avg Active DL UEs | T4-Traffic | 2.41 | 2.18 | 2.35 | −9.5% | −1.83 | +1.83 | ≥1σ 🟡 |

---

## Sigma_Chart sheet

Data table (columns A–C) feeds a horizontal bar chart:

| Column | Header |
|--------|--------|
| A | `KPI` |
| B | `σ (chart)` — degradation-positive value |
| C | `Tier` |

Sorted by \|σ\| descending so the top movers appear at the top of the chart.

**Example top rows:**

| KPI | σ (chart) | Tier |
|-----|-----------|------|
| NGAP Setup SR | +4.79 | T3 |
| Radio Admission NSA | +4.25 | T3 |
| Active E-RAB Drop | +3.62 | T3 |
| Avg CQI 256QAM | −3.58 | T2 |
| CB RACH SR | +2.91 | T3 |
| Avg MAC Tput DL | +2.61 | T1-Tput |
| PDSCH Slot Usage | +2.17 | T1-ES |

---

## Per_Carrier_Detail sheet

Selected T1 KPIs (those with per-carrier scientific interest) broken down by carrier.

**Default per-carrier KPIs:**
- ReducedTX Ratio
- DRX Sleep Ratio
- PDSCH Slot Usage
- Avg DL Delay CU-UP
- Avg MAC Tput DL
- PDCCH CCE Starvation

**Column layout:**

| Column | Header |
|--------|--------|
| A | `KPI` |
| B | `N28 Baseline` |
| C | `N28 Trial` |
| D | `N28 σ` |
| E | `N78_F1 Baseline` |
| F | `N78_F1 Trial` |
| G | `N78_F1 σ` |
| … | *(three columns per additional carrier)* |

**Example rows** (values anonymised):

| KPI | N28 BL | N28 Trial | N28 σ | N78\_F1 BL | N78\_F1 Trial | N78\_F1 σ |
|-----|--------|-----------|-------|------------|--------------|----------|
| DRX Sleep Ratio | 49.86 | 50.08 | −0.48 | 51.20 | 50.57 | +0.72 |
| PDSCH Slot Usage | 20.45 | 20.44 | +0.02 | 41.07 | 36.75 | +1.85 |
| Avg DL Delay CU-UP | 50.16 | 46.55 | −0.55 | 36.10 | 39.64 | +0.46 |
| Avg MAC Tput DL | 0.594 | 0.436 | +2.93 | 0.884 | 0.657 | +2.17 |
| PDCCH Starvation | 0.157 | 0.184 | +2.76 | 2.073 | 2.436 | +1.39 |

---

## Energy_Saving sheet

Top table: statistical summary for ES KPIs (same column layout as Significance_Matrix).

**Default ES KPIs:**

| Nokia column | Display name | Tier |
|-------------|-------------|------|
| `[N]RU_ENERGY_CONSUMPTION` | RU Energy Consumption | T1-ES |
| `[N]RU_AVG_PWR_USAGE` | RU Avg Power Usage | T1-ES |
| `[N]RU_MAX_PWR_USAGE` | RU Max Power Usage | T2 |
| `[N]RU_MIN_PWR_USAGE` | RU Min Power Usage | T2 |
| `[N]ENERGY_CONSUMPTION_IN_SM` | System Module Energy | T1-ES |
| `[N]ENERGY_CONSUMPTION_IN_RF` | RF Energy | T1-ES |
| `[N]ENERGY_CONSUMPTION_IN_BTS` | Total BTS Energy | T1-ES |
| `[N]MAX_INPUT_VOLTAGE_IN_RF` | Max RF Input Voltage | T4-Traffic |

**Example rows** (values anonymised):

| KPI | Tier | Baseline | Trial | Post-RB | Δ% | σ (raw) | σ (chart) |
|-----|------|----------|-------|---------|-----|---------|-----------|
| RU Energy Consumption | T1-ES | 142 495 945 | 144 518 673 | 146 459 401 | +1.42% | +0.58 | +0.58 |
| Total BTS Energy | T1-ES | 218 340 120 | 221 674 389 | 224 105 667 | +1.53% | +0.62 | +0.62 |
| RU Avg Power Usage | T1-ES | 1 425 473 315 | 1 445 706 781 | 1 465 381 602 | +1.42% | +0.59 | +0.59 |

Below the table: daily trajectory charts for each ES KPI (same line + marker format as KPI_Grouped BTS_Energy tab).

---

## KPI_Trajectories sheet

Carrier-stratified daily time-series for feature causal-chain KPIs, driven by `feature_context.json`.

- One chart per T1 KPI defined in `feature_context.json → t1_carrier_kpis`
- Each chart: one coloured line per carrier + red Trial-start bar + green Rollback bar
- Charts labelled with category: `mechanism` / `outcome` / `quality` / `watchdog` / `traffic_context`

> To populate this sheet you must provide a `feature_context.json` file. Use
> `scripts/nr/feature_context_template.json` as the starting template and fill in the KPI list
> from the Nokia feature document. Claude can generate this automatically from the DN PDF.
