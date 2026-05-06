# NR KPI Charts Excel — Output Structure Reference

**File:** `CBXXXXXX_<RC>_NR_KPI_Grouped.xlsx`  
**Script:** `scripts/nr/build_kpi_charts_nr.py`  
**One file per RC** (e.g. RC1 and RC2 produced separately).

---

## Sheet inventory (24 sheets)

| # | Sheet name | Type | Content |
|---|-----------|------|---------|
| 1 | `Cover` | Metadata | Trial summary: ID, feature, technology, dates |
| 2 | `Agg_Data` | Data | Raw aggregated daily KPI values (all carriers and columns) |
| 3 | `D_EnergySaving` | Data (hidden) | Energy-saving KPI time-series — feeds C_EnergySaving |
| 4 | `C_EnergySaving` | Charts | DRX Sleep Ratio, ReducedTX Ratio, PDSCH Slot Usage trends |
| 5 | `D_Latency` | Data (hidden) | Latency KPI time-series |
| 6 | `C_Latency` | Charts | Avg DL Delay in CU-UP, Avg UL Reorder Delay trends |
| 7 | `D_Throughput` | Data (hidden) | Throughput KPI time-series |
| 8 | `C_Throughput` | Charts | Avg MAC Tput DL, Max DL PDCP Tput trends |
| 9 | `D_Accessibility` | Data (hidden) | Accessibility KPI time-series |
| 10 | `C_Accessibility` | Charts | Accessibility SR, NGAP Setup SR, RRC Setup SR trends |
| 11 | `D_Retainability` | Data (hidden) | Retainability KPI time-series |
| 12 | `C_Retainability` | Charts | QoS Flow Drop (RAN), Active E-RAB Drop, SgNB Abn Release trends |
| 13 | `D_EN_DC` | Data (hidden) | EN-DC / SgNB KPI time-series |
| 14 | `C_EN_DC` | Charts | SgNB Add Prep SR, SgNB Reconfig SR, PSCell Chg SR trends |
| 15 | `D_PDCCH` | Data (hidden) | PDCCH watchdog KPI time-series |
| 16 | `C_PDCCH` | Charts | Avg PDCCH CCE Starvation Ratio trend (watchdog) |
| 17 | `D_Mobility` | Data (hidden) | Mobility / handover KPI time-series |
| 18 | `C_Mobility` | Charts | Intra-DU IF HO SR, Xn Inter-gNB HO SR, Inter-gNB HO NSA trends |
| 19 | `D_RadioQuality` | Data (hidden) | Radio quality KPI time-series |
| 20 | `C_RadioQuality` | Charts | Avg CQI 256QAM, Avg SINR PUSCH, Avg Pathloss trends |
| 21 | `D_Traffic` | Data (hidden) | Traffic / load KPI time-series |
| 22 | `C_Traffic` | Charts | PRB Util DL/UL, Avg Active DL UEs, DL Data Volume trends |
| 23 | `D_BTS_Energy` | Data (hidden) | BTS / RU energy time-series from ES cluster export |
| 24 | `C_BTS_Energy` | Charts | Total BTS Energy, RU Energy Consumption, RU Avg Power trends |

---

## Cover sheet

| Row | Column A | Column B |
|-----|----------|----------|
| 1 | `5G NR KPI Performance Report — RC1  (CBXXXXXX)` | *(merged title)* |
| 2 | `Trial ID:` | `CBXXXXXX` |
| 3 | `Feature:` | `<feature name> (NR NSA)` |
| 4 | `Technology:` | `NR NSA (EN-DC)` |
| 5 | `Trial implementation:` | `DD Month YYYY` |
| 6 | `Trial rollback:` | `DD Month YYYY` (or `—` if no rollback) |
| 7 | `Carriers:` | `N28, N78_F1, N78_F2, N78_F3` (example) |
| 8 | `Generated:` | `<timestamp>` |

---

## Agg_Data sheet — column layout

| Column | Nokia export column name | Notes |
|--------|--------------------------|-------|
| A | `Date` | `DATETIME` normalised to midnight |
| B | `Carrier` | Band label (e.g. N28, N78\_F1, N78\_F2, N78\_F3) |
| C | `Cell availability ratio` | % |
| D | `Cell availability ratio excluding planned unavailability periods` | % |
| E | `Cell in Reduced TX Power Saving Mode Ratio` | % — primary ES indicator |
| F | `Accessibility success ratio` | % |
| G | `Initial UE message sent success ratio` | % |
| H | `NGAP connection establishment success ratio` | % |
| … | *(~70 additional Nokia NR columns)* | All columns present in the source export |

**Example rows** (values anonymised):

| Date | Carrier | Cell Avail (%) | ReducedTX (%) | Accessibility SR (%) | NGAP SR (%) |
|------|---------|---------------|---------------|----------------------|-------------|
| YYYY-MM-DD | N28 | 100.00 | 0.00 | 98.21 | 99.88 |
| YYYY-MM-DD | N78\_F1 | 100.00 | 0.00 | 94.12 | 99.79 |
| YYYY-MM-DD | N78\_F2 | 95.80 | 0.00 | 98.61 | 99.91 |
| YYYY-MM-DD | N28 | 100.00 | 4.31 | 98.47 | 99.85 |
| YYYY-MM-DD | N78\_F1 | 100.00 | 3.97 | 94.55 | 99.81 |

*(Rows for `N78_F3` may be sparse or all-zero if that carrier was not fully active during the trial period.)*

---

## Chart tab structure (C_ sheets)

Each `C_<group>` sheet contains a stack of line charts, one per KPI in the group. Every chart shows:

- **One coloured line per carrier** (e.g. N28, N78\_F1, N78\_F2, N78\_F3)
- **Red bar** at trial start date (y2-axis 0→1 column marker)
- **Green bar** at rollback date (y2-axis 0→1 column marker; omitted if `TRIAL_ROLLBACK = None`)
- Both event markers combined in a **single `combine()` call** (xlsxwriter bug fix — see CHANGELOG)
- X-axis: daily dates, 7-day major tick
- Y-axis: KPI value, `#,##0.00` format

**Chart groups and representative KPIs:**

| Tab group | Representative KPIs shown |
|-----------|--------------------------|
| `C_EnergySaving` | DRX Sleep Ratio, ReducedTX Ratio, PDSCH Slot Usage |
| `C_Latency` | Avg DL Delay CU-UP, Avg UL Reorder Delay |
| `C_Throughput` | Avg MAC Tput DL, Max DL PDCP Tput, Max Cell Tput DL |
| `C_Accessibility` | Accessibility SR, NGAP Setup SR, RRC Setup SR, QoS Flow Setup SR |
| `C_Retainability` | QoS Flow Drop (RAN), Active E-RAB Drop, SgNB Abn Release, UE Abn Release |
| `C_EN_DC` | SgNB Add Prep SR, SgNB Reconfig SR, SgNB Xfer Fail, PSCell Chg SR |
| `C_PDCCH` | PDCCH CCE Starvation (watchdog) |
| `C_Mobility` | Intra-DU IF HO SR, Xn Inter-gNB HO SR, Inter-gNB HO NSA |
| `C_RadioQuality` | Avg CQI 256QAM, Avg SINR PUSCH R1/R2, Avg Pathloss PUSCH, Avg PHR |
| `C_Traffic` | PRB Util DL/UL, Avg Active DL/UL UEs, DL/UL Data Volume |
| `C_BTS_Energy` | Total BTS Energy, RU Energy, RU Avg/Min/Max Power (from ES export) |

---

## Carrier colour coding (NR — example)

| Carrier | Colour |
|---------|--------|
| N28 | `#D62728` (red) |
| N78\_F1 | `#1F77B4` (blue) |
| N78\_F2 | `#2CA02C` (green) |
| N78\_F3 | `#9467BD` (purple) |

> Update `CARRIER_ORDER`, `CARRIER_COLORS`, and `MNO_NR_NRARFCN_MAP` in the configuration
> section of `build_kpi_charts_nr.py` to match your cluster's carriers and NRARFCNs.

---

## Key difference from LTE output

| Feature | LTE | NR |
|---------|-----|----|
| Carrier stratification | Feature bands vs Unaffected bands (H1/H2/H3) | All carriers are Feature scope (H0 — no control group) |
| Chart groups | 10 groups (incl. ENDC, MCS) | 11 groups (incl. EN-DC, PDCCH watchdog, BTS Energy) |
| Rollback marker colour | Blue bar | Green bar |
| ES data source | Separate `extract_energy_stats.py` output | Integrated from ES cluster export in `build_kpi_charts_nr.py` |
