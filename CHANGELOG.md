# Changelog — ran-trial-production

All notable changes to this skill are documented in this file.

---

## [1.1.0] — 2026-04-26

### Fixed — xlsxwriter `combine()` single-call bug

**Root cause:** `xlsxwriter` only honours **one** `combine()` call per chart object. If you call `lc.combine(bc_trial)` followed by `lc.combine(bc_rb)`, the second call silently overwrites the first, leaving only the rollback marker visible and discarding the trial-start marker entirely.

**Wrong pattern (< v1.1.0):**
```python
bc_trial = wb.add_chart({'type': 'column'})
bc_trial.add_series({...red fill..., 'y2_axis': True})
lc.combine(bc_trial)           # ← first combine

bc_rb = wb.add_chart({'type': 'column'})
bc_rb.add_series({...green fill..., 'y2_axis': True})
lc.combine(bc_rb)              # ← second combine — silently overwrites the first!
```

**Fixed pattern (v1.1.0+):**
```python
bc_markers = wb.add_chart({'type': 'column'})
bc_markers.add_series({...red fill..., 'y2_axis': True})    # Trial-start marker
bc_markers.add_series({...green fill..., 'y2_axis': True})  # Rollback marker
lc.combine(bc_markers)         # ← single combine — both series included
```

**Files changed:** `scripts/nr/build_kpi_charts_nr.py`, `scripts/nr/build_stats_report_nr.py` — all chart-building functions updated.

### Added

- 3-phase support (Baseline / Trial / Post-RB) with conditional Post-RB handling when `TRIAL_ROLLBACK = None`
- Row shading in D-tabs: yellow = Trial, light green = Post-RB
- Per-RC processing via `RCS` list and `SUBNETWORK` column filter
- ES data filtered per RC from the ES cluster export
- KPI_Trajectories sheet driven by `feature_context.json` causal-chain definition

---

## [1.0.0] — 2026-03-01

### Added

- Initial release: LTE production pipeline (fully implemented)
- NR NSA Phase 3 skeleton: KPI Charts + Statistical Analysis + Technical Memo
- Interactive HTML intake form (LTE + NR, multi-phase support)
- Markdown intake template
- Methodology reference documents (RAT-agnostic + NR-specific departures)
- BTS-level sanity check procedure (Departure 7 in methodology_nr.md)
