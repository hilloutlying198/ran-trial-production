# LTE KPI Charts Excel — Output Structure Reference

**File:** `CBXXXXXX_<RC>_KPI_Grouped.xlsx`  
**Script:** `scripts/lte/build_kpi_charts_template.py`  
**One file per RC** (e.g. RC1 and RC2 produced separately).

---

## Sheet inventory (22 sheets)

| # | Sheet name | Type | Content |
|---|-----------|------|---------|
| 1 | `Cover` | Metadata | Trial summary: ID, feature, dates, source file |
| 2 | `Agg_Data` | Data | Raw aggregated daily KPI values (all carriers, all columns) |
| 3 | `D_EnergySaving` | Data (hidden) | Energy saving KPI time-series — feeds C_EnergySaving charts |
| 4 | `C_EnergySaving` | Charts | PSM Ratio, ReducedTX Ratio, DRX Sleep Ratio trends |
| 5 | `D_Accessibility` | Data (hidden) | Accessibility KPI time-series |
| 6 | `C_Accessibility` | Charts | Cell Availability, RRC SR, E-RAB Setup SR trends |
| 7 | `D_Retainability` | Data (hidden) | Retainability KPI time-series |
| 8 | `C_Retainability` | Charts | E-RAB Retainability, Drop Ratio trends |
| 9 | `D_Traffic` | Data (hidden) | Traffic KPI time-series |
| 10 | `C_Traffic` | Charts | RRC Attempts, Active UEs, Data Volume trends |
| 11 | `D_Handover` | Data (hidden) | Handover KPI time-series |
| 12 | `C_Handover` | Charts | Intra-eNB HO SR, Inter-eNB HO SR trends |
| 13 | `D_Throughput` | Data (hidden) | Throughput KPI time-series |
| 14 | `C_Throughput` | Charts | PDCP Active Cell Tput DL/UL, PRB Utilisation trends |
| 15 | `D_Quality` | Data (hidden) | Radio quality KPI time-series |
| 16 | `C_Quality` | Charts | Avg CQI, UL rBLER, MCS DL trends |
| 17 | `D_ENDC` | Data (hidden) | EN-DC / SgNB KPI time-series |
| 18 | `C_ENDC` | Charts | SgNB Addition SR, SgNB Release Ratio trends |
| 19 | `D_MCS_Radio` | Data (hidden) | MCS and radio link parameter time-series |
| 20 | `C_MCS_Radio` | Charts | Avg MCS DL/UL, Avg CQI, SINR trends |
| 21 | `D_Latency` | Data (hidden) | Latency KPI time-series |
| 22 | `C_Latency` | Charts | Avg Latency DL, PDCP SDU Delay trends |

---

## Cover sheet

| Row | Column A | Column B |
|-----|----------|----------|
| 1 | `4G KPI Performance Report — RC1` | *(merged title)* |
| 2 | `Source file:` | `4G_System_Program_Nokia_<dates>_RC1.xlsx` |
| 3 | `Trial feature:` | `<feature name and parameter>` |
| 4 | `Trial implementation:` | `DD Month YYYY` |
| 5 | `Trial rollback:` | `DD Month YYYY` |
| 6 | `Data period:` | `DD Mon YYYY → DD Mon YYYY (daily)` |
| 7 | `Generated:` | `<timestamp>` |

---

## Agg_Data sheet — column layout

The raw daily aggregated data used to feed all chart tabs.

| Column | Nokia export column name | Notes |
|--------|--------------------------|-------|
| A | `Date` | `DATETIME` normalised to midnight |
| B | `Carrier` | Band label (e.g. B800, B900, B1800, B2100, B700, B2300_F1, B2300_F2) |
| C | `Cell Availability Ratio` | % |
| D | `Cell in Power Saving Mode Ratio` | % — primary energy KPI |
| E | `Cell in Reduced TX Power Saving Mode Ratio` | % — secondary energy KPI |
| F | `RACH Setup Attempts` | Count |
| G | `RACH Setup Completion Success Rate` | % |
| H | `Complete Contention Based RACH Setup Success Rate` | % |
| I | `Total RRC Connection Setup Attempts` | Count |
| J | `Total RRC Connection Setup Success Ratio` | % |
| … | *(~50 additional Nokia KPI columns)* | All columns present in the source export |

**Example rows** (values anonymised):

| Date | Carrier | Cell Avail (%) | PSM Ratio (%) | ReducedTX (%) | RACH Attempts | RACH SR (%) |
|------|---------|----------------|---------------|---------------|---------------|-------------|
| YYYY-MM-DD | B800 | 99.71 | 0.00 | 32.10 | 1 245 000 | 98.92 |
| YYYY-MM-DD | B900 | 99.83 | 0.00 | 28.75 | 8 320 000 | 99.14 |
| YYYY-MM-DD | B1800 | 66.25 | 33.40 | 0.00 | 480 000 | 95.21 |
| YYYY-MM-DD | B2100 | 99.27 | 0.00 | 31.60 | 50 100 000 | 99.35 |
| YYYY-MM-DD | B700 | 99.90 | 0.00 | 0.00 | 3 100 000 | 99.52 |

---

## Chart tab structure (C_ sheets)

Each `C_<group>` sheet contains a stack of line charts, one per KPI in the group. Every chart shows:

- **One coloured line per carrier** (7 LTE carriers: B700, B800, B900, B1800, B2100, B2300\_F1, B2300\_F2)
- **Red bar** at trial implementation date (y2-axis 0→1 column marker)
- **Blue/green bar** at rollback date (y2-axis 0→1 column marker)
- X-axis: daily dates, 7-day major tick
- Y-axis: KPI value with appropriate number format

**Chart groups and representative KPIs:**

| Tab group | Representative KPIs shown |
|-----------|--------------------------|
| `C_EnergySaving` | PSM Ratio, ReducedTX Ratio, DRX Sleep Ratio |
| `C_Accessibility` | Cell Availability, RRC SR, E-RAB Setup SR, RACH SR |
| `C_Retainability` | E-RAB Retainability (GBR), Drop Ratio, UE Context SR |
| `C_Traffic` | RRC Attempts, Active UEs, DL Data Volume |
| `C_Handover` | Intra-eNB HO SR, Inter-eNB HO SR, X2 HO SR |
| `C_Throughput` | PDCP Active Cell Tput DL, PRB Utilisation DL/UL |
| `C_Quality` | Avg CQI, UL rBLER, DL rBLER, Avg MCS DL |
| `C_ENDC` | SgNB Addition SR, SgNB Release Ratio, EPS Fallback |
| `C_MCS_Radio` | Avg MCS DL/UL, Avg SINR, Avg CQI |
| `C_Latency` | Avg Latency DL, PDCP SDU Delay DL |

---

## Carrier colour coding (LTE)

| Carrier | Colour |
|---------|--------|
| B700 | `#D62728` (red) |
| B800 | `#1F77B4` (blue) |
| B900 | `#2CA02C` (green) |
| B1800 | `#9467BD` (purple) |
| B2100 | `#8C564B` (brown) |
| B2300\_F1 | `#E377C2` (pink) |
| B2300\_F2 | `#17BECF` (teal) |

> Update `CARRIER_ORDER` and `CARRIER_COLORS` in the configuration section of
> `build_kpi_charts_template.py` to match your cluster's carriers.
