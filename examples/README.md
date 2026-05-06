# Output Examples — ran-trial-production

This directory contains **anonymised reference outputs** produced by the skill pipeline from
real trial data. All operator names, trial IDs, feature parameters, and dates have been
replaced with generic placeholders (MNO / CBXXXXXX / YYYY-MM-DD). KPI values and chart
structures are real and representative.

Use these files to:
- Understand the exact sheet structure and column layout before running your own trial
- Verify your outputs match the expected structure after adapting the scripts
- Share with colleagues as a format reference without exposing trial data

---

## LTE example outputs

| File | Description | Size |
|------|-------------|------|
| [`lte/CBXXXXXX_RC3_KPI_Grouped.xlsx`](lte/CBXXXXXX_RC3_KPI_Grouped.xlsx) | LTE KPI Charts — RC3 (22 sheets, 10 chart groups, 7 carriers) | ~640 KB |
| [`lte/CBXXXXXX_RC4_KPI_Grouped.xlsx`](lte/CBXXXXXX_RC4_KPI_Grouped.xlsx) | LTE KPI Charts — RC4 (same structure) | ~645 KB |
| [`lte/CBXXXXXX_Statistical_Analysis.xlsx`](lte/CBXXXXXX_Statistical_Analysis.xlsx) | LTE Statistical Analysis (6 sheets: Significance Matrix, Band Comparison, Ranking) | ~42 KB |

**Script that produces these:** `scripts/lte/build_kpi_charts_template.py` and
`scripts/lte/build_stats_report_template.py`

**Structure reference:** [`lte/kpi_grouped_structure.md`](lte/kpi_grouped_structure.md) and
[`lte/statistical_analysis_structure.md`](lte/statistical_analysis_structure.md)

---

## NR (5G NSA) example outputs

| File | Description | Size |
|------|-------------|------|
| [`nr/CBXXXXXX_RC3_NR_KPI_Grouped.xlsx`](nr/CBXXXXXX_RC3_NR_KPI_Grouped.xlsx) | NR KPI Charts — RC3 (24 sheets, 11 chart groups, 4 carriers) | ~251 KB |
| [`nr/CBXXXXXX_RC4_NR_KPI_Grouped.xlsx`](nr/CBXXXXXX_RC4_NR_KPI_Grouped.xlsx) | NR KPI Charts — RC4 (same structure) | ~227 KB |
| [`nr/CBXXXXXX_RC3_NR_Statistical_Analysis.xlsx`](nr/CBXXXXXX_RC3_NR_Statistical_Analysis.xlsx) | NR Statistical Analysis — RC3 (9 sheets: Overview, Significance Matrix, Energy Saving, KPI Trajectories) | ~67 KB |
| [`nr/CBXXXXXX_RC4_NR_Statistical_Analysis.xlsx`](nr/CBXXXXXX_RC4_NR_Statistical_Analysis.xlsx) | NR Statistical Analysis — RC4 (same structure) | ~66 KB |

**Script that produces these:** `scripts/nr/build_kpi_charts_nr.py` and
`scripts/nr/build_stats_report_nr.py`

**Structure reference:** [`nr/kpi_grouped_structure.md`](nr/kpi_grouped_structure.md) and
[`nr/statistical_analysis_structure.md`](nr/statistical_analysis_structure.md)

---

## What is anonymised

| Original | Replaced with |
|----------|--------------|
| Trial IDs (e.g. CB009333) | `CBXXXXXX` |
| Feature document references | `DNXXXXXXXXX` |
| Operator name | `MNO` |
| Feature parameter names | `featureParam` |
| Trial / baseline / rollback dates | `YYYY-MM-DD` |
| Source file names with dates | `..._<dates>_RC3.xlsx` |

KPI **values** and **chart data** are from the real trial and are preserved as-is —
they are not operator-identifying.

---

## Structure reference documents

| File | Description |
|------|-------------|
| [`lte/kpi_grouped_structure.md`](lte/kpi_grouped_structure.md) | Full sheet inventory and column map for LTE KPI Charts Excel |
| [`lte/statistical_analysis_structure.md`](lte/statistical_analysis_structure.md) | Full sheet inventory and column map for LTE Statistical Analysis Excel |
| [`nr/kpi_grouped_structure.md`](nr/kpi_grouped_structure.md) | Full sheet inventory and column map for NR KPI Charts Excel |
| [`nr/statistical_analysis_structure.md`](nr/statistical_analysis_structure.md) | Full sheet inventory and column map for NR Statistical Analysis Excel |
