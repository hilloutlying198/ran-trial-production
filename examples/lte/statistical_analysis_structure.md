# LTE Statistical Analysis Excel — Output Structure Reference

**File:** `CBXXXXXX_Statistical_Analysis.xlsx`  
**Script:** `scripts/lte/build_stats_report_template.py`  
**One file covers all RCs** (RC1 and RC2 side-by-side in most sheets).

---

## Sheet inventory (6 sheets)

| # | Sheet name | Content |
|---|-----------|---------|
| 1 | `Significance_Matrix` | Per-KPI: Baseline / Trial / Post-RB means, Δ%, σ (raw), significance level — Feature bands only |
| 2 | `Sigma_Charts` | Ranked bar chart: chart-sigma (degradation-positive) for all KPIs, RC1 vs RC2 columns |
| 3 | `Period_Trajectories` | Baseline → Trial → Post-RB mean table, showing recovery or persistence of effects |
| 4 | `Band_Comparison` | Feature bands vs Unaffected bands side-by-side — key for H1/H2/H3 hypothesis assessment |
| 5 | `Per_Carrier_Detail` | Selected KPIs broken down per individual carrier for both RCs |
| 6 | `Significance_Ranking` | All KPIs ranked by |σ| descending, RC1 and RC2 columns |

---

## Significance_Matrix — column layout

Title row: `CBXXXXXX — Trial Statistical Analysis: Feature Bands (B800 / B900 / B1800 / B2100)`  
Subtitle: `<parameter> = <value>  |  Baseline: DD Mon–DD Mon  |  Trial: DD Mon–DD Mon`

| Column | Header | Format | Notes |
|--------|--------|--------|-------|
| A | `KPI (RC1 Feature Bands)` | Text | Short display name |
| B | `Tier` | Text | T1-ES / T1-Lat / T1-Tput / T2 / T3 / T4-Traffic; colour-coded background |
| C | `Baseline` | `#,##0.000` | Mean over baseline window, feature bands only |
| D | `Trial` | `#,##0.000` | Mean over trial window, feature bands only |
| E | `Post-RB` | `#,##0.000` | Mean over post-rollback window (or `n/a` if no rollback) |
| F | `Δ%` | `+0.00%;-0.00%` | (Trial − Baseline) / Baseline |
| G | `σ` | `+0.00;-0.00` | (Trial mean − Baseline mean) / Baseline std dev; degradation-positive |
| H | `Signif.` | Text | `≥3σ` / `≥2σ` / `≥1σ` / `<1σ` — colour-coded cell |

**Example rows** (values anonymised):

| KPI | Tier | Baseline | Trial | Post-RB | Δ% | σ | Signif. |
|-----|------|----------|-------|---------|-----|---|---------|
| PSM Ratio | T1-ES | 0.000 | 1.912 | 0.000 | +∞ | +0.9 | ≥1σ 🟡 |
| ReducedTX Ratio | T1-ES | 0.000 | 2.218 | 0.000 | +∞ | +0.6 | <1σ |
| DRX Sleep Ratio | T1-ES | 42.30 | 42.84 | 42.15 | +1.3% | +0.5 | <1σ |
| E-RAB Retain. Fail | T3 | 1.239 | 1.553 | 2.329 | +25.3% | +3.7 | ≥3σ 🔴 |
| UL rBLER | T2 | 0.949 | 0.993 | 1.017 | +4.6% | +2.3 | ≥2σ 🟠 |
| HO Intra-eNB SR | T3 | 99.41 | 99.22 | 98.70 | −0.19% | +0.9 | <1σ |
| Avg CQI | T2 | 8.72 | 8.68 | 8.71 | −0.5% | −0.3 | <1σ |

**Significance colour legend:**

| Threshold | Degradation colour | Improvement colour |
|-----------|-------------------|--------------------|
| ≥ 3σ | `#C00000` red (white text) | `#006100` dark green (white text) |
| ≥ 2σ | `#E26B0A` orange | `#548235` mid green |
| ≥ 1σ | `#FFC000` yellow | `#9BC2E6` light blue |
| < 1σ | `#F0F0F0` grey | `#F0F0F0` grey |

---

## Sigma_Charts — column layout

| Column | Content |
|--------|---------|
| A | KPI name |
| B | RC1 σ (degradation-positive: positive = worse) |
| C | RC2 σ (degradation-positive) |
| D | Reference line at ±2 (for chart formatting) |
| E | *(spacer)* |
| F | KPI name (for Δ% table) |
| G | RC1 Δ% |
| H | RC2 Δ% |

A horizontal bar chart spans columns E onwards, sorted by |σ| descending. Each bar represents one KPI.

---

## Period_Trajectories — column layout

| Column | Header | Notes |
|--------|--------|-------|
| A | `KPI` | Short display name |
| B | `Baseline` | Mean over baseline window |
| C | `Trial` | Mean over trial window |
| D | `Post-RB` | Mean over post-rollback window |
| E | `Δ% (Trial)` | Trial vs Baseline |

**Example rows:**

| KPI | Baseline | Trial | Post-RB | Δ% (Trial) |
|-----|----------|-------|---------|------------|
| E-RAB Retain. Fail (%) | 1.239 | 1.553 | 2.329 | +25.3% |
| UL rBLER (%) | 0.949 | 0.993 | 1.017 | +4.6% |
| PSM Ratio (%) | 0.000 | 1.912 | 0.000 | — |
| Avg CQI | 8.72 | 8.68 | 8.71 | −0.5% |

---

## Band_Comparison — column layout (LTE-specific)

Compares Feature bands vs Unaffected bands — the H1/H2/H3 framework depends on this.

| Column | Header | Notes |
|--------|--------|-------|
| A | `KPI` | Short display name |
| B | `Feat. BL` | Feature band baseline mean |
| C | `Feat. Trial` | Feature band trial mean |
| D | `Feat. Δ%` | |
| E | `Feat. σ` | Degradation-positive |
| F | `Unaff. BL` | Unaffected band baseline mean |
| G | `Unaff. Trial` | Unaffected band trial mean |
| H | `Unaff. Δ%` | |
| I | `Unaff. σ` | Degradation-positive |

**Example row:**

| KPI | Feat. BL | Feat. Trial | Feat. Δ% | Feat. σ | Unaff. BL | Unaff. Trial | Unaff. Δ% | Unaff. σ |
|-----|----------|-------------|----------|---------|-----------|-------------|----------|---------|
| E-RAB Retain. Fail | 1.239 | 1.553 | +25.3% | +3.7 | 1.946 | 2.652 | +36.3% | +3.2 |
| UL rBLER | 0.949 | 0.993 | +4.6% | +2.3 | 1.012 | 1.316 | +30.0% | +5.8 |

> Degradation on unaffected bands at the same or greater magnitude indicates H2 (concurrent
> trend) rather than H1 (feature-induced). This is the critical signal for a confounding-factor verdict.

---

## Per_Carrier_Detail — column layout

| Column | Content |
|--------|---------|
| A | `Carrier` (e.g. B800, B900, B1800, B2100) |
| B–D | RC1 Baseline / Trial / Δ% |
| E–G | RC2 Baseline / Trial / Δ% |

**Example (QCI8 DL Latency ms):**

| Carrier | RC1 Baseline | RC1 Trial | RC1 Δ% | RC2 Baseline | RC2 Trial | RC2 Δ% |
|---------|-------------|-----------|--------|-------------|-----------|--------|
| B800 | 162.1 | 159.9 | −1.4% | 220.9 | 215.4 | −2.5% |
| B900 | 132.6 | 130.5 | −1.6% | 179.0 | 175.6 | −1.9% |
| B1800 | 118.3 | 115.7 | −2.2% | 157.2 | 154.1 | −2.0% |
| B2100 | 44.1 | 43.6 | −1.1% | 61.8 | 60.2 | −2.6% |

---

## Significance_Ranking — column layout

All KPIs sorted by |σ| descending. Used to identify the top movers.

| Column | Header |
|--------|--------|
| A | `KPI` |
| B | `Tier` |
| C | `RC1 σ (deg+)` |
| D | `RC1 Δ%` |
| E | `RC2 σ (deg+)` |
| F | `RC2 Δ%` |

**Example top rows:**

| KPI | Tier | RC1 σ | RC1 Δ% | RC2 σ | RC2 Δ% |
|-----|------|-------|--------|-------|--------|
| E-RAB Retain. Fail | T3 | +3.7 | +25.3% | +0.2 | +4.6% |
| UL rBLER | T2 | +2.3 | +4.6% | +0.7 | +1.8% |
| HO Intra-eNB SR | T3 | +0.9 | −0.19% | +3.2 | −0.81% |
| RRC SR | T3 | +1.2 | −0.03% | +3.8 | −0.07% |
| PSM Ratio | T1-ES | −0.5 | +1.9% | −0.1 | +0.6% |
| ReducedTX Ratio | T1-ES | −0.6 | +2.2% | −0.5 | +2.5% |
