# Nokia 5G NR KPI Column Map — Example MNO NSA cluster

Reference file mapping Nokia 5G System Program export column names to display names,
tiers, and a `higher_bad` flag (True = higher value is worse, for sigma normalisation).

**Scope:** NSA/EN-DC deployment, Nokia AirScale, Rel. 26R1-SR or later.

**Status:** Mechanical map covering all columns found in the reference export
`5G_System_Program_Nokia_20260323_20260417_cluster_per_carrier.xlsx` (132 columns).
Tier assignments marked with **[PDF-seeded]** are derived from the µDTX feature
document predictions and need confirmation per trial; tier assignments marked
**[default]** are placeholders that must be reviewed by the engineer before first use.

---

## Tier definitions (copy of `methodology.md` intent)

| Tier | Meaning | Used for |
|------|---------|----------|
| T1-ES | Primary — Energy Saving | Measuring the feature's intended benefit |
| T1-Lat | Primary — Latency | KPIs the feature expects to change |
| T1-Tput | Primary — Throughput | KPIs the feature expects to change |
| T2 | Secondary | Correlated KPIs; support interpretation |
| T3 | Watchdog | Must not degrade |
| T4-Traffic | Context | Traffic profile sanity checks |
| EXCL | Excluded | Column always empty or not applicable in this cluster |

---

## µDTX feature expected impacts (from Nokia feature document)

The Nokia feature document makes these explicit predictions. KPIs below are
tiered as T1 candidates on that basis.

1. **DL user throughput expected to DECREASE.** Source: Section 3, quote: "KPI
   NR_5100c 5G Average MAC layer user throughput in downlink is expected to
   decrease due to aggregating small packets into bigger chunks and increasing
   additional waiting time for scheduling."
2. **PDSCH OFDM symbol time expected to DECREASE.** Source: Section 3, same paragraph.
3. **End-to-end delay:** may degrade under the predecessor feature alone, but is expected to IMPROVE slightly
   under the enhanced variant, but **must be monitored**. Source: Section 3.
4. **Energy consumption expected to DECREASE.** Source: Section 6 (benefit of the feature).
5. **PDCCH blocking rate may INCREASE** in cells with limited PDCCH capacity.
   Source: Section 3.

---

## Full column map

### Identifier columns (not KPIs)

| # | Nokia column | Display | Type |
|---|---|---|---|
| 0 | `DATETIME` | DateTime | identifier |
| 1 | `NRARFCN` | NR-ARFCN | identifier |

### Availability (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 2 | `Cell availability ratio` | Cell Availability | T3 | False |
| 3 | `Cell availability ratio excluding planned unavailability periods` | Cell Availability (excl planned) | T3 | False |

### Power saving / energy (T1-ES — PRIMARY per PDF) **[PDF-seeded]**

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 4 | `Cell in Reduced TX Power Saving Mode Ratio` | ReducedTX Ratio | T1-ES | False | Higher = more power saving |
| 129 | `DRX sleep time ratio` | DRX Sleep Ratio | T1-ES | False | Higher = UE-side power saving |
| 130 | `[NOK_5G]SAMPLES_NR_CELL_POWER_SAVING` | NR Cell PS Samples | T4-Traffic | False | Counter, context only |
| 131 | `[NOK_5G]CHNG_TO_NR_CELL_POWER_SAVING` | NR Cell PS Changes | T4-Traffic | False | Counter, context only |

### Accessibility — combined and component (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 5 | `Accessibility success ratio` | Accessibility SR | T3 | False |
| 6 | `Initial UE message sent success ratio` | Init UE Msg SR | T3 | False |
| 7 | `NGAP connection establishment success ratio` | NGAP Setup SR | T3 | False |
| 8 | `QoS Flow Setup Attempts` | QoS Flow Setup Att | T4-Traffic | False |
| 9 | `QoS Flow Setup Success Ratio` | QoS Flow Setup SR | T3 | False |
| 10 | `Number of PDU session resource setup requests` | PDU Session Setup Req | T4-Traffic | False |
| 11 | `Non_Stand Alone call accessibility 5G side` | NSA Call Access SR | T3 | False |
| 22 | `Total number of RRC connection establishment attempts` | RRC Setup Attempts | T4-Traffic | False |
| 23 | `RRC connection establishment success ratio` | RRC Setup SR | T3 | False |
| 24 | `Initial E_RAB Setup Success Ratio` | Init E-RAB SR | T3 | False |
| 25 | `Initial E_RAB Setup Attempts` | Init E-RAB Att | T4-Traffic | False |
| 26 | `UE context setup success ratio` | UE Ctx Setup SR | T3 | False |
| 27 | `Radio admission success ratio for NSA user` | Radio Admission SR NSA | T3 | False |
| 28 | `Number of radio admission requests for NSA user` | Radio Admission Req NSA | T4-Traffic | False |
| 29 | `Admission control rejection ratio due to lack of PUCCH resources` | PUCCH Resource Reject (NSA) | T2 | True |
| 30 | `Radio admission success ratio for SA users` | Radio Admission SR SA | T3 | False |
| 31 | `Number of radio admission requests for SA users` | Radio Admission Req SA | T4-Traffic | False |
| 32 | `Admission control rejection ratio due to lack of PUCCH resources.1` | PUCCH Resource Reject (SA) | T2 | True |

### EN-DC / SgNB (T3 — watchdog, NSA-specific)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 12 | `Number of SgNB addition requests` | SgNB Add Req | T4-Traffic | False |
| 13 | `SgNB addition preparation success ratio` | SgNB Add Prep SR | T3 | False |
| 14 | `Status Transfer failure ratio during SgNB Addition` | SgNB Status Xfer Fail | T3 | True |
| 15 | `Status Transfer received ratio during SgNB addition` | SgNB Status Xfer Rcvd | T3 | False |
| 16 | `SgNB reconfiguration success ratio` | SgNB Reconfig SR | T3 | False |

### RACH (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 17 | `Active RACH setup success ratio` | Active RACH SR | T3 | False |
| 18 | `Contention based RACH setup success ratio` | CB RACH SR | T3 | False |
| 19 | `Contention based RACH setup attempts` | CB RACH Att | T4-Traffic | False |
| 20 | `Contention free RACH setup success ratio` | CF RACH SR | T3 | False |
| 21 | `Contention free RACH setup attempts` | CF RACH Att | T4-Traffic | False |

### Retainability / drops (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 33 | `QoS Flow Drop Ratio _ RAN view` | QoS Flow Drop (RAN) | T3 | True |
| 34 | `QoS Flow Drop Ratio _ User view_double_Ng mapped to UE lost` | QoS Flow Drop (User-UE Lost) | T3 | True |
| 35 | `Normal gNB_initiated release ratio _ RAN view` | Normal gNB Release | T4-Traffic | False |
| 36 | `Active QoS Flow Drop Ratio_double_Ng mapped to UE lost` | Active QoS Flow Drop (UE Lost) | T3 | True |
| 37 | `Active E_RAB Drop Ratio _ SgNB view` | Active E-RAB Drop (SgNB) | T3 | True |
| 38 | `SgNB triggered abnormal release ratio excluding X2 reset` | SgNB Abnormal Release | T3 | True |
| 39 | `Ratio of SgNB releases initiated by SgNB due to radio connection with UE lost` | SgNB Rel UE Lost | T3 | True |
| 40 | `Ratio of UE releases due to abnormal reasons` | UE Abnormal Release | T3 | True |
| 41 | `Ratio of SgNB releases initiated by LTE eNB` | SgNB Rel by eNB | T4-Traffic | False |
| 42 | `Ratio of SgNB releases initiated by SgNB due to UE inactivity` | SgNB Rel UE Inactive | T4-Traffic | False |
| 43 | `Ratio of SgNB releases initiated by SgNB due to A2 measurement` | SgNB Rel A2 Meas | T4-Traffic | False |
| 44 | `Number of UE releases due to radio link failure` | RLF UE Releases | T3 | True |

### VoNR (5QI 1) — may be EXCL on low-traffic clusters **[warning: 93% NaN in reference data]**

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 45 | `Number of 5QI_1 QoS flow setup attempts excluding fallback` | VoNR Flow Att (excl fb) | T4-Traffic | False | 27% NaN |
| 46 | `5QI_1 QoS flow setup success ratio excluding fallback` | VoNR Flow SR (excl fb) | T3 | False | 27% NaN |
| 47 | `Number of 5QI_1 QoS Flows Setup Attempts` | VoNR Flow Att | T4-Traffic | False | |
| 48 | `5QI_1 QoS Flows Setup Success Ratio` | VoNR Flow SR | T3 | False | |
| 49 | `5QI1 QoS Flow Drop Ratio _ RAN view` | VoNR Drop (RAN) | T3 | True | 93% NaN, may EXCL |
| 50 | `5QI1 QoS Flow Drop Ratio _ User view_double_Ng mapped to UE lost` | VoNR Drop (User-UE Lost) | T3 | True | 93% NaN, may EXCL |
| 51 | `Number of UE redirections to E_UTRAN due to voice fallback to LTE` | EPS Fallback Redirections | T3 | True | Fewer = more VoNR retained |

### GBR / VoNR traffic context

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 52 | `Number of GBR DRB radio admission requests` | GBR DRB Req | T4-Traffic | False | |
| 53 | `Average GBR call holding time per cell` | Avg GBR Hold Time | T4-Traffic | False | 93% NaN |
| 54 | `Peak GBR call holding time` | Peak GBR Hold Time | T4-Traffic | False | |
| 55 | `GBR traffic load in Erlang` | GBR Load (Erlang) | T4-Traffic | False | |
| 56 | `Average number of active VoNR UEs in selected area` | Avg Active VoNR UEs | T4-Traffic | False | |

### Mobility — intra-gNB (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 57 | `Intra_cell handover preparation attempts` | Intra-Cell HO Prep Att | T4-Traffic | False | |
| 58 | `Intra_cell handover total success ratio` | Intra-Cell HO SR | T3 | False | 100% NaN, likely EXCL |
| 59 | `Intra_frequency Intra_gNB Intra_DU handover preparation attempts` | Intra-DU Intra-Freq HO Prep | T4-Traffic | False | |
| 60 | `Intra_frequency Intra_gNB Intra_DU handover total success ratio` | Intra-DU Intra-Freq HO SR | T3 | False | |
| 61 | `Intra_Frequency Intra_gNB Inter_DU handover preparation attempts` | Inter-DU Intra-Freq HO Prep | T4-Traffic | False | |
| 62 | `HO total success ratio Intra_Frequency Intra_gNB Inter_DU` | Inter-DU Intra-Freq HO SR | T3 | False | 100% NaN, EXCL |
| 65 | `Intra_gNB Intra_DU Inter_frequency HO preparation attempts per PLMN` | Intra-DU Inter-Freq HO Prep | T4-Traffic | False | |
| 66 | `Intra_gNB Intra_DU Inter_frequency HO preparation success ratio per PLMN` | Intra-DU Inter-Freq HO Prep SR | T3 | False | 50% NaN |
| 67 | `Intra_gNB Intra_DU Inter_frequency HO total success ratio per PLMN` | Intra-DU Inter-Freq HO SR | T3 | False | 50% NaN |

### Mobility — inter-gNB (T3 — watchdog)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 63 | `Intra_frequency Xn based Inter_gNB handover execution attempts per PLMN` | Xn Inter-gNB HO Exec Att | T4-Traffic | False | |
| 64 | `Intra_frequency Xn based Inter_gNB handover execution success ratio per PLMN` | Xn Inter-gNB HO Exec SR | T3 | False | |
| 68 | `Xn based Inter_gNB Inter_frequency HO execution attempts per PLMN` | Xn Inter-gNB Inter-Freq HO Att | T4-Traffic | False | |
| 69 | `Xn based Inter_gNB Inter_frequency HO execution success ratio per PLMN` | Xn Inter-gNB Inter-Freq HO SR | T3 | False | |
| 73 | `Inter gNB handover attempts for NSA` | Inter-gNB HO Att (NSA) | T4-Traffic | False | |
| 74 | `Inter gNB handover success ratio for NSA` | Inter-gNB HO SR (NSA) | T3 | False | |
| 75 | `Number of inter_frequency intra_DU handover preparation attempts for NSA` | Inter-Freq Intra-DU HO Prep (NSA) | T4-Traffic | False | |
| 76 | `Inter_frequency intra_DU handover preparation success ratio for NSA` | Inter-Freq Intra-DU HO Prep SR (NSA) | T3 | False | 25% NaN |
| 77 | `Inter_frequency intra_DU handover total success ratio for NSA` | Inter-Freq Intra-DU HO SR (NSA) | T3 | False | 25% NaN |

### Mobility — PSCell change (NSA-specific, T3 watchdog)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 70 | `Number of intra frequency intra DU PSCell change preparation attempts for NSA 3x` | PSCell Change Prep Att | T4-Traffic | False | |
| 71 | `Intra_frequency intra_DU PSCell change preparation success ratio` | PSCell Change Prep SR | T3 | False | |
| 72 | `Intra_frequency intra_DU PSCell change total success ratio` | PSCell Change SR | T3 | False | |
| 78 | `Inter_gNB Inter_Frequency PSCell Change on source gNB_SN Initiated Change` | Inter-gNB PSCell Change (SN) | T4-Traffic | False | 100% NaN, EXCL |
| 79 | `Inter_gNB Inter_Frequency PSCell Change Success Ratio on source Gnb_SN Initiated Change` | Inter-gNB PSCell Change SR (SN) | T3 | False | 100% NaN, EXCL |
| 80 | `Inter_gNB Inter_Frequency PSCell Change Total Success Ratio on source gNB_SN Initiated Change` | Inter-gNB PSCell Change Total SR (SN) | T3 | False | 100% NaN, EXCL |

### Latency (T1-Lat — PRIMARY per PDF) **[PDF-seeded]**

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 81 | `Average delay DL in CU_UP per cell` | Avg DL Delay CU-UP | T1-Lat | True | PDF: may be impacted by µDTX |
| 82 | `Average PDCP re_ordering delay in the UL per cell` | Avg UL PDCP Reorder Delay | T2 | True | |

### Radio quality (T2 — secondary)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 83 | `Average wideband CQI 64QAM table` | Avg CQI (64QAM) | T2 | False |
| 84 | `Average wideband CQI 256QAM table` | Avg CQI (256QAM) | T2 | False |
| 85 | `Average UE related SINR for PUSCH in Rank 1` | Avg SINR PUSCH R1 | T2 | False |
| 86 | `Average UE related SINR for PUSCH in Rank 2` | Avg SINR PUSCH R2 | T2 | False |
| 87 | `Average UE related RSSI for PUSCH` | Avg RSSI PUSCH | T2 | False |
| 88 | `Average UE related SINR for PUCCH` | Avg SINR PUCCH | T2 | False |
| 89 | `Average UE related RSSI for PUCCH` | Avg RSSI PUCCH | T2 | False |
| 90 | `Average UE power headroom for PUSCH calculated from histogram counters` | Avg PHR PUSCH | T2 | False |
| 91 | `Average UE pathloss level for PUSCH` | Avg Pathloss PUSCH | T2 | True |

### Throughput and data volume (T1-Tput — PRIMARY per PDF) **[PDF-seeded]**

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 92 | `MAC SDU data volume transmitted in DL on DTCH` | DL Data Volume | T4-Traffic | False | Traffic context |
| 93 | `MAC SDU data volume received in UL on DTCH` | UL Data Volume | T4-Traffic | False | Traffic context |
| 94 | `Average MAC layer user throughput in downlink` | Avg MAC Tput DL | T1-Tput | False | PDF: expected to DECREASE |
| 95 | `Maximum DL PDCP SDU NR leg throughput per DRB` | Max DL PDCP Tput NR Leg | T2 | False | |
| 96 | `Maximum MAC SDU Cell Throughput in DL on DTCH` | Max MAC Cell Tput DL | T2 | False | |
| 97 | `Maximum MAC SDU Cell Throughput in UL on DTCH` | Max MAC Cell Tput UL | T2 | False | |

### MCS / modulation (T2 — secondary)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 98 | `Average MCS used in downlink for PDSCH with 64QAM table` | Avg MCS DL 64QAM | T2 | False |
| 99 | `Average MCS used in downlink for PDSCH with 256QAM table` | Avg MCS DL 256QAM | T2 | False |
| 100 | `Average rank used in downlink` | Avg DL Rank | T2 | False |
| 101 | `Average MCS used in uplink for PUSCH with 64QAM table` | Avg MCS UL 64QAM | T2 | False |
| 102 | `Average MCS used in uplink for PUSCH with 256QAM table` | Avg MCS UL 256QAM | T2 | False |

### PRB and slot utilisation (T2 — secondary; relevant to µDTX)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 103 | `PRB utilization for PDSCH` | PRB Util DL | T2 | False | Traffic sanity |
| 104 | `PRB utilization for PUSCH` | PRB Util UL | T2 | False | Traffic sanity |
| 105 | `Average number of MU_MIMO eligible UEs per DL PRB` | Avg MU-MIMO UEs/PRB | T2 | False | 100% NaN, EXCL |
| 106 | `Usage ratio of PDSCH data slots over all DL data slots` | PDSCH Slot Usage | T1-ES | False | **[PDF-seeded]** Related to PDSCH OFDM symbol time — expected to DECREASE per PDF |
| 107 | `Usage ratio of PUSCH data slots over all UL data slots` | PUSCH Slot Usage | T2 | False | |

### PDCCH (T2 — secondary; µDTX WATCHDOG risk) **[PDF-seeded]**

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 108 | `Average aggregation level used on PDCCH uplink grants` | Avg PDCCH AGG UL | T2 | False | |
| 109 | `Average aggregation level used on PDCCH downlink grants` | Avg PDCCH AGG DL | T2 | False | |
| 110 | `Average PDCCH CCE starvation ratio in cell` | PDCCH CCE Starvation | T3 | True | **PDF: may INCREASE under µDTX** — treat as watchdog |

### Users / load (T4-Traffic — context)

| # | Nokia column | Display | Tier | higher_bad |
|---|---|---|---|---|
| 111 | `Average number of active UEs with data in the buffer for DRBs in DL` | Avg Active DL UEs | T4-Traffic | False |
| 112 | `Average number of active UEs with data in the buffer for DRBs in UL` | Avg Active UL UEs | T4-Traffic | False |
| 113 | `Maximum number of active UEs with data in the buffer for DRBs in DL` | Max Active DL UEs | T4-Traffic | False |
| 114 | `Maximum number of active UEs with data in the buffer for DRBs in UL` | Max Active UL UEs | T4-Traffic | False |
| 115 | `Average number of NSA users in selected area` | Avg NSA Users | T4-Traffic | False |
| 116 | `Maximum number of NSA users per cell` | Max NSA Users | T4-Traffic | False |
| 117 | `Average number of SA RRC connected users in selected area` | Avg SA RRC Conn Users | T4-Traffic | False |
| 118 | `Average number of SA non_GBR users in selected area` | Avg SA non-GBR Users | T4-Traffic | False |
| 119 | `Maximum number of SA RRC connected users` | Max SA RRC Conn Users | T4-Traffic | False |
| 120 | `Maximum number of SA users with non_GBR DRBs` | Max SA non-GBR Users | T4-Traffic | False |

### Carrier aggregation (T2 — secondary; relevant to µDTX `caSupportEnabled`)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 121 | `Downlink carrier aggregation reconfiguration success ratio` | DL CA Reconfig SR | T3 | False | 25% NaN |
| 122 | `Downlink carrier aggregation reconfiguration attempts` | DL CA Reconfig Att | T4-Traffic | False | |
| 123 | `Uplink carrier aggregation reconfiguration success ratio` | UL CA Reconfig SR | T3 | False | 100% NaN, EXCL |
| 124 | `Uplink carrier aggregation reconfiguration attempts` | UL CA Reconfig Att | T4-Traffic | False | |
| 125 | `Average number of activated SCells in downlink` | Avg DL SCells | T2 | False | |
| 126 | `Average number of activated SCells in uplink` | Avg UL SCells | T2 | False | |

### DSS (n28 only — context)

| # | Nokia column | Display | Tier | higher_bad | Notes |
|---|---|---|---|---|---|
| 127 | `DSS Allocation ratio of DL slots assigned to NR` | DSS DL Allocation NR | T4-Traffic | False | n28 only, 75% NaN (expected) |
| 128 | `DSS Allocation ratio of UL PRBs assigned to NR` | DSS UL Allocation NR | T4-Traffic | False | n28 only, 75% NaN (expected) |

---

## Energy-saving KPIs — from ES report (separate data source)

The Nokia 5G System Program export does **not** contain direct per-kWh energy
measurements. Those live in the ES (Energy Saving) report, which is cluster-level
only — per-carrier breakdown is not possible because the underlying counters are
at BTS level.

**Placeholder for ES columns** (to be confirmed on first run with the real ES file):

| Placeholder name | Expected Nokia name or concept | Tier | higher_bad | Aggregation |
|---|---|---|---|---|
| `ES_TOTAL_ENERGY_KWH` | Total BTS energy consumed (kWh) | T1-ES | True | SUM over period |
| `ES_AVG_POWER_W` | Average BTS power consumption (W) | T1-ES | True | MEAN over period |
| `ES_POWER_SAVING_PCT` | Power saving vs reference baseline | T1-ES | False | MEAN |
| `ES_DATA_VOLUME_GB` | Data volume processed (GB) | T4-Traffic | False | SUM |
| `ES_ENERGY_EFFICIENCY` | Bits-per-joule or similar | T1-ES | False | derived |

**Action required on first run:** before running `extract_stats.py` for the first time
on real ES data, review the ES report's actual column names and update
`NR_ES_COLUMN_MAP` in `scripts/nr/extract_stats.py` accordingly. The current placeholders
will not match any real export. This is documented as a known gap in the skill.

---

## EXCL columns in current reference cluster (100% NaN)

These columns returned zero data in the reference export for the analysis period.
`extract_stats.py` will automatically drop them with a printed warning; the tier
assignments above are preserved so the dict can be reused if a different cluster or
time window does populate them.

- `Intra_cell handover total success ratio` (col 58)
- `HO total success ratio Intra_Frequency Intra_gNB Inter_DU` (col 62)
- `Average number of MU_MIMO eligible UEs per DL PRB` (col 105)
- `Uplink carrier aggregation reconfiguration success ratio` (col 123)
- `Inter_gNB Inter_Frequency PSCell Change on source gNB_SN Initiated Change` (col 78)
- `Inter_gNB Inter_Frequency PSCell Change Success Ratio on source Gnb_SN Initiated Change` (col 79)
- `Inter_gNB Inter_Frequency PSCell Change Total Success Ratio on source gNB_SN Initiated Change` (col 80)

---

## Aggregation rules

Same as LTE conventions with NR-specific adjustments:

- **SUM** over time: attempt counts, data volumes, session counts
  (keywords: "number of", "attempts", "data volume", "requests")
- **MEAN** over time: ratios, rates, success ratios, drop ratios, delays, SINR, CQI, MCS,
  rank, utilisation, pathloss, power saving ratio, DRX sleep ratio
- **MAX** over time: peak values (keywords: "maximum", "peak")

NR-specific: PSCell change KPIs aggregate MEAN (they are ratios despite "Change" in the
name). DSS allocation ratios aggregate MEAN and should be filtered to n28 only in charts.

---

## Maintenance notes

- When Nokia adds a new KPI in a future SR release, add a row here AND in
  `NR_COLUMN_MAP` in `scripts/nr/extract_stats.py`. The two must stay in sync.
- The 100% NaN list may differ per cluster. Do not permanently delete rows from this
  file based on one cluster's behaviour; they are retained so the same map works across
  clusters.
- Tiers marked `[PDF-seeded]` should not be changed without a corresponding update to
  the PDF source quote. Tiers marked `[default]` are placeholders — review on first trial.
