# MNO Network Carrier Allocation — 4G LTE

Reference file derived from `Carrier_allocation.xlsx`.
**Only carriers marked MNO are used in KPI reports.** All other rows must be filtered out of source data before aggregation.

## MNO Carrier Map (EARFCN → Carrier Label)

| Carrier Label | Band | EARFCN | BW (MHz) | Operator |
|---|---|---|---|---|
| B700      |  700 MHz |  9260 | 10 | MNO ✓ |
| B800      |  800 MHz |  6400 | 10 | MNO ✓ |
| B900      |  900 MHz |  3725 | 10 | MNO ✓ |
| B1800     | 1800 MHz |  1226 |  5 | MNO ✓ |
| B2100     | 2100 MHz |   347 | 10 | MNO ✓ |
| B2300_F1  | 2300 MHz | 39250 | 20 | MNO ✓ |
| B2300_F2  | 2300 MHz | 39448 | 20 | MNO ✓ |

## Excluded Carriers (Non-MNO)

| Band | EARFCN | Operator | Reason |
|---|---|---|---|
| B800  | 6300 | Other MNO | Other MNO — exclude |
| B900  | 3507 | Other MNO | Other MNO — exclude |
| B900  | 3501 | Unknown | Not in allocation — exclude |
| B900  | 3500 | Unknown | Not in allocation — exclude |
| B2100 | 223  | Other MNO | Other MNO — exclude |
| B2100 | 247  | Other MNO | Other MNO — exclude |
| B2100 | 372  | Unknown | Not in allocation — exclude |
| B2600 | 2850 | Unknown | Not in allocation — exclude |

## Notes

- **B2300 is two separate MNO carriers** (F1 and F2, both 20 MHz). They must **not** be aggregated together — doing so causes ratio KPIs (e.g. ERAB_Init) to exceed 100% because numerator and denominator scale differently across 2 cells.
- **B1800 is a 5 MHz carrier** (single cell per site). All others are 10–20 MHz.
- **NB-IoT rows** (BAND = NaN, EARFCN = NaN) are always excluded.
- RC4 source file contains B2600 EARFCN 2850 — this is **not MNO** and must be excluded.

## Processing Rule

```python
MNO_EARFCN_MAP = {
    9260:  'B700',
    6400:  'B800',
    3725:  'B900',
    1226:  'B1800',
    347:   'B2100',
    39250: 'B2300_F1',
    39448: 'B2300_F2',
}
# Filter:  df = df[df['EARFCN'].isin(MNO_EARFCN_MAP.keys())]
# Label:   df['CARRIER'] = df['EARFCN'].map(MNO_EARFCN_MAP)
# Aggregate by (DATETIME, CARRIER): SUM for counters, MEAN for ratios/rates
```

## Carrier Display Order

`B700 → B800 → B900 → B1800 → B2100 → B2300_F1 → B2300_F2`
