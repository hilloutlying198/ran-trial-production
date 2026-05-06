# MNO Network Carrier Allocation — 5G NR

Reference file derived from the MNO cluster carrier allocation spreadsheet.
**Scope:** 5G NR NSA (EN-DC) cluster. Update with your cluster's actual NRARFCNs before first use.
Only carriers listed here are included in NR KPI reports. Any row whose `NRARFCN` is not
in this map must be filtered out before aggregation.

## MNO NR Carrier Map (NRARFCN → Carrier Label)

> **Replace the example values below with your cluster's actual NRARFCNs and band labels.**

| Carrier Label | NR Band | NRARFCN | Band Group | Operator |
|---|---|---|---|---|
| N28       | n28 |  152600 | n28 | MNO ✓ |
| N78_F1    | n78 |  635334 | n78 | MNO ✓ |
| N78_F2    | n78 |  650666 | n78 | MNO ✓ |
| N78_F3    | n78 |  652000 | n78 | MNO ✓ |

The `Band Group` column exists so that downstream analysis can collapse multiple carriers
in the same band into a single aggregate when the per-carrier view would otherwise add
noise. It is **not** used for feature vs unaffected stratification — see notes below.

## Stratification note — carrier-only, no Feature/Unaffected split

The LTE production module stratifies KPIs into Feature Bands vs Unaffected Bands because
some LTE trials change parameters on specific EARFCNs. **This does not apply to NR trials
where the feature is a cell-level toggle applied uniformly to all NR cells in the cluster.**

Per the Nokia feature document (Section 6.1 in typical µDTX feature docs), when a feature is
activated via an NRCELL-level parameter, it applies uniformly to all NR cells in the trial
cluster. There is therefore no in-cluster control group of NR carriers.

**Consequences for the NR memo:**
- The H1/H2/H3 hypothesis framework used for LTE retainability analysis is **not directly
  applicable**. The H-framework depends on a within-cluster unaffected-band control.
- Detection of concurrent network effects (H2) for NR requires either:
  - an external control (e.g., a neighbouring NR cluster outside the trial), or
  - the LTE anchor-leg behaviour during the same window (for EN-DC; anchor-leg KPIs live
    in a separate LTE report that is not part of this NR data source).
- Absent either control, the NR verdict rests on pre/post comparison within the same
  carriers, which is weaker evidence than LTE's dual-control design. State this caveat
  explicitly in the memo's Data Quality Assessment section.

If a future NR trial is carrier-selective (e.g., feature enabled only on n78 and not n28),
update this file to add a `role` column with Feature/Unaffected values and re-enable the
H-framework. The carrier map format is compatible with that extension.

## Excluded carriers

None in the example cluster — all 4 carriers in the MNO NR cluster are in-scope. If the Nokia export
contains NRARFCNs not in the map above, they must be filtered out before aggregation.
If new NR carriers are added to the cluster, add rows here and to
`MNO_NR_NRARFCN_MAP` in `scripts/nr/extract_stats.py`.

## Processing rule

```python
MNO_NR_NRARFCN_MAP = {
    152600: 'N28',    # ← replace with your cluster's NRARFCNs
    635334: 'N78_F1',
    650666: 'N78_F2',
    652000: 'N78_F3',
}
MNO_NR_BAND_GROUP = {
    'N28':    'n28',
    'N78_F1': 'n78',
    'N78_F2': 'n78',
    'N78_F3': 'n78',
}
# Filter:     df = df[df['NRARFCN'].isin(MNO_NR_NRARFCN_MAP.keys())]
# Label:      df['CARRIER'] = df['NRARFCN'].map(MNO_NR_NRARFCN_MAP)
# Band group: df['BAND_GROUP'] = df['CARRIER'].map(MNO_NR_BAND_GROUP)
# Aggregate by (DATETIME, CARRIER): SUM for counters, MEAN for ratios/rates (see methodology)
```

## Carrier Display Order

`N28 → N78_F1 → N78_F2 → N78_F3`

Low-band first, then sub-6 in NRARFCN-ascending order.

## Operator-specific notes (example — replace with your cluster's specifics)

- **n28**: 5 MHz or 10 MHz DSS carrier on low-band. DSS counters
  (`DSS Allocation ratio of DL slots assigned to NR`,
  `DSS Allocation ratio of UL PRBs assigned to NR`) are populated on this carrier
  and not on n78. This is expected behaviour, not a data quality issue.
- **n78**: Three sub-6 carriers, typical TDD mid-band 5G. VoNR (5QI_1) KPIs may have
  very low sample counts on low-traffic clusters — see `kpi_column_map.md` for handling.

## Source

Generated from the MNO carrier allocation spreadsheet. Note: some Nokia export templates
label the NRARFCN column as `EARFCN` — a leftover from LTE intake templates. Keep `NRARFCN`
as the canonical name in all scripts and references.
