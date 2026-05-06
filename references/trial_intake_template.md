# Trial Intake Template
# Fill in all sections before handing to Claude. Delete placeholder comments.
# Required fields are marked [REQUIRED]. Optional fields can be left blank.

---

## 1. Trial Metadata

```
TRIAL_ID:          # [REQUIRED] Short identifier used in file names, e.g. CBXXXXXX
FEATURE_NAME:      # [REQUIRED] Full feature/parameter name, e.g. "allowTrafficConcentration"
PARAMETER_BEFORE:  # [REQUIRED] Value before trial, e.g. 1
PARAMETER_AFTER:   # [REQUIRED] Value during trial, e.g. 0
VENDOR:            # e.g. Nokia
NETWORK:           # e.g. MNO 4G
```

## 2. Software Versions Under Test

```
RC1_LABEL:    # e.g. RC3 (label used in outputs)
RC1_SW_VER:   # e.g. Nokia SW 22.1.3
RC2_LABEL:    # e.g. RC4 (leave blank if single-RC trial)
RC2_SW_VER:   # e.g. Nokia SW 22.2.1
```

## 3. Trial Periods

```
BASELINE_START:   # YYYY-MM-DD
BASELINE_END:     # YYYY-MM-DD
TRIAL_START:      # YYYY-MM-DD
TRIAL_END:        # YYYY-MM-DD
POST_RB_START:    # YYYY-MM-DD (leave blank if no rollback period)
POST_RB_END:      # YYYY-MM-DD
```

## 4. Band Assignments

```
FEATURE_BANDS:    # [REQUIRED] Comma-separated, e.g. B800, B900, B1800, B2100
                  # These are bands where the parameter was ACTUALLY CHANGED

UNAFFECTED_BANDS: # [REQUIRED] Comma-separated, e.g. B700, B2300_F1, B2300_F2
                  # These are bands in the cluster where parameter was NOT changed
```

---

## 5. Raw Data Files [REPLACES manual KPI tables]

If you provide the Nokia KPI engine exports, Claude will compute all KPI statistics
(means, sigmas, band comparisons, per-carrier values) automatically using extract_stats.py.
You do NOT need to fill in Sections 5/6/7 manually.

```
RC1_FILE:   # [REQUIRED] Path to RC1 Nokia KPI export, e.g. /path/to/RC3_export.xlsx
RC2_FILE:   # Path to RC2 Nokia KPI export (leave blank if single-RC trial)
```

**If files are not available** (e.g. you only have aggregated summary values), fill in
Sections 5-manual, 6-manual, 7-manual below instead.

---

## 5-manual. KPI Statistics (fill only if no raw files)

Provide these only if you cannot supply raw Nokia exports.
Sigma = (trial_mean - baseline_mean) / baseline_std_dev

| KPI | Tier | Higher=Bad? | RC1 BL | RC1 Tr | RC1 PostRB | RC1 σ | RC2 BL | RC2 Tr | RC2 PostRB | RC2 σ |
|-----|------|-------------|--------|--------|------------|-------|--------|--------|------------|-------|
| PSM Ratio % | T1-PS | No | | | | | | | | |
| ReducedTX Ratio % | T1-PS | No | | | | | | | | |
| DRX Sleep Ratio % | T1-PS | No | | | | | | | | |
| Avg Latency DL ms | T1-Lat | Yes | | | | | | | | |
| SDU Delay QCI1 ms | T1-Lat | Yes | | | | | | | | |
| SDU Delay QCI8 ms | T1-Lat | Yes | | | | | | | | |
| UL rBLER % | T2 | Yes | | | | | | | | |
| DL rBLER % | T2 | Yes | | | | | | | | |
| Avg UL MCS | T2 | No | | | | | | | | |
| DL Spectral Eff bps/Hz | T2 | No | | | | | | | | |
| Tput DL Active Mbps | T2 | No | | | | | | | | |
| Tput UL Active Mbps | T2 | No | | | | | | | | |
| Cell Availability % | T3 | No | | | | | | | | |
| RACH SR % | T3 | No | | | | | | | | |
| E-RAB SR % | T3 | No | | | | | | | | |
| RRC SR % | T3 | No | | | | | | | | |
| E-RAB Drop Ratio % | T3 | Yes | | | | | | | | |
| ERAB Retain. Fail % | T3 | Yes | | | | | | | | |
| HO Intra-eNB SR % | T3 | No | | | | | | | | |

---

## 6-manual. Band Comparison (fill only if no raw files)

| KPI | RC1 Feat BL | RC1 Feat Tr | RC1 Feat σ | RC1 Unaff BL | RC1 Unaff Tr | RC1 Unaff σ | RC2 Feat BL | RC2 Feat Tr | RC2 Feat σ | RC2 Unaff BL | RC2 Unaff Tr | RC2 Unaff σ |
|-----|-------------|-------------|------------|--------------|--------------|-------------|-------------|-------------|------------|--------------|--------------|-------------|
| ERAB Retain. Fail % | | | | | | | | | | | | |
| UL rBLER % | | | | | | | | | | | | |
| E-RAB Drop Ratio % | | | | | | | | | | | | |
| Cell Availability % | | | | | | | | | | | | |
| PSM Ratio % | | | | | | | | | | | | |

---

## 7-manual. Per-Carrier Detail (fill only if no raw files)

| KPI | Band | RC1 BL | RC1 Tr | RC2 BL | RC2 Tr |
|-----|------|--------|--------|--------|--------|
| DRX Sleep % | B800 | | | | |
| DRX Sleep % | B900 | | | | |
| DRX Sleep % | B1800 | | | | |
| DRX Sleep % | B2100 | | | | |
| Latency DL ms | B800 | | | | |
| Latency DL ms | B900 | | | | |
| Latency DL ms | B1800 | | | | |
| Latency DL ms | B2100 | | | | |
| QCI8 Delay ms | B800 | | | | |
| QCI8 Delay ms | B900 | | | | |
| QCI8 Delay ms | B1800 | | | | |
| QCI8 Delay ms | B2100 | | | | |
| PSM Ratio % | B900 | | | | |
| PSM Ratio % | B1800 | | | | |
| ReducedTX % | B2100 | | | | |

---

## 8. Confounding Events (Optional but Important)

List any known events during the trial window that may explain KPI changes:

```
- [Date] [Description] — affects [bands/carriers/RC]
- e.g. 2026-02-10 RC4 software upgrade on B2300 cells — affects RC4 unaffected bands
- e.g. 2026-02-15 Public holiday — potential traffic reduction
```

## 9. Preliminary Verdict (Optional)

If you already have a verdict from the ran-trial-analysis skill or from your own review,
state it here so the report frames the analysis around it:

```
VERDICT:           # e.g. PASS WITH CONDITIONS
VERDICT_REASONING: # 1-2 sentences
```

---

## 10. Output Preferences

```
OUTPUT_DIR:        # Path where files should be saved (defaults to workspace folder)
INCLUDE_POST_RB:   # Yes / No — whether to include Post-RB period in charts
CHART_STYLE:       # Standard / Minimal (Standard = full 54-chart KPI workbook)
```
