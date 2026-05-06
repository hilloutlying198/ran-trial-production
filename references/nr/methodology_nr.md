# NR Methodology Addendum — NSA / EN-DC Trials

This file is the NR counterpart to `references/methodology.md`. It references that
file for anything that is RAT-agnostic (sigma math, verdict tiers, near-zero-variance
handling) and **documents the NR-specific departures** clearly.

Read `methodology.md` first for shared principles. This file covers only what differs
for NR NSA.

---

## Departure 1: No Feature/Unaffected band stratification

The LTE methodology (Section "Band Stratification") mandates separating Feature Bands
from Unaffected Bands in every KPI table. **This does not apply to NR trials where the
feature is a cell-level toggle applied uniformly to all NR cells, and must not be
mechanically carried over.**

**Why:** When a Nokia feature doc (e.g., Section 6.1) specifies activation via
an NRCELL-level parameter such as `actEnhDtxOptimizedScheduler`, the toggle applies
uniformly to all NR cells in the trial cluster. There is therefore no in-cluster
unaffected control group.

**What to do instead:**
- Stratify KPIs by **carrier only** (N28 vs N78_F1 vs N78_F2 vs N78_F3, or collapsed
  into band groups using the band group column).
- The primary comparison is **pre-trial baseline vs trial period**, within each carrier.
- Optionally, if requested, compare NR-cluster trend against a control cluster outside
  the trial scope (this is external and must be user-provided).

**What NOT to do:**
- Do NOT invent a "feature/unaffected" split by, e.g., treating n28 as unaffected and
  n78 as feature — unless the feature document explicitly specifies carrier-selective
  activation.
- Do NOT apply the H1/H2/H3 framework. It depends on an in-cluster control.

---

## Departure 2: H-Hypothesis framework deferred

For LTE trials with Feature/Unaffected split, the H-framework distinguishes:
- H1 (Feature-induced) — feature bands degrade, unaffected bands stable
- H2 (Concurrent network trend) — both groups degrade similarly
- H3 (RC-specific SW interaction) — one RC's unaffected bands degrade

**NR equivalent:** none available within a single-cluster NSA trial of a
non-carrier-selective feature. The NR memo's Data Quality Assessment section
must explicitly state:

> "Concurrent network effects cannot be distinguished from feature effects using
> the in-cluster data alone. Verdict is based on pre/post comparison with this
> caveat. External controls (neighbouring NR cluster, LTE anchor-leg behaviour
> during the same window) would be needed to rule out concurrent effects but
> are not in scope."

This is not a failure of rigour — it is an honest statement of what the data design
supports. A PASS verdict on NR data alone is weaker evidence than an LTE PASS with
dual controls, and the memo must say so.

---

## Departure 3: Trial window structure — single-RC, simpler structure

If the trial includes multiple software releases (RC3 and RC4, etc.), analyse each
RC independently. **For NR, assume single-RC unless the user specifies otherwise.**

Expected NR period structure:

| Period | Purpose | Typical length |
|---|---|---|
| Baseline | Pre-feature activation | ≥ 7 days |
| Trial    | Feature active | ≥ 14 days for statistical stability |
| Post-RB (optional) | After feature deactivation | ≥ 7 days |

The boundary between baseline and trial **must be confirmed by the user**. Do not
infer it from filename dates or activity patterns — the skill's pre-flight check
requires explicit confirmation.

If the user reports multiple RCs (e.g., feature tested on two software builds), the
NR code paths do support it — `extract_stats.py` accepts `--rc2-file` exactly like the
LTE version — but single-RC is the simpler default.

---

## Departure 4: ES (energy-saving) data is a separate source, cluster-level only

Unlike LTE trials where all KPIs come from the Nokia system program export, NR
trials often have **two data sources**:

1. **5G System Program cluster-per-carrier export** — per-carrier, daily, covering
   accessibility/retainability/mobility/throughput/PDCCH/etc.
2. **ES (Energy Saving) cluster report** — cluster-level only, daily energy counters

ES data cannot be broken down by carrier (underlying counters are at BTS level).
Consequences:

- In the stats Excel, ES KPIs appear **only** in cluster-level sheets, never in
  per-carrier charts.
- In the memo, ES KPIs get a dedicated Section 4.x labelled "Energy Saving Impact
  (Cluster Level)".
- `extract_stats.py` accepts the two files independently via `--kpi-file` and
  `--es-file` flags; either can be omitted, and the resulting stats Excel will
  simply omit that section.

The specific ES column names vary by Nokia SW release and must be confirmed on first
run (see `references/nr/kpi_column_map.md` — "Energy-saving KPIs" section).

---

## Departure 5: Aggregation of VoNR / 5QI1 KPIs in low-traffic clusters

Some clusters show very high NaN rates for 5QI1 drop-ratio columns (very low VoNR traffic).
Two handling rules:

1. **If a KPI is ≥ 80% NaN across both baseline and trial in a carrier**, compute the
   aggregate and flag in the report: "Sample size too small for reliable
   significance." Do not report a sigma; report absolute count deltas only.
2. **If a KPI is ≥ 80% NaN in baseline but populated in trial (or vice versa)**,
   treat as a reporting-gap anomaly, flag in Data Quality Assessment, and do not
   compute sigma.

This is stricter than the LTE rule because NR 5QI1 samples are genuinely sparse,
not a data quality artefact.

---

## Departure 6: Feature Causal Chain — KPI_Trajectories Selection

### Principle

The `KPI_Trajectories` sheet in the Statistical Analysis Excel is **not** a generic
display of high-sigma KPIs. It is a structured narrative of the feature's expected
causal chain, read directly from the Nokia feature document (DN number / PDF).

**Why this matters:** A high-sigma KPI list tells an engineer what moved statistically.
A causal-chain list tells them whether the feature is working as designed — which is the
question the trial is actually trying to answer. These are different questions with
different KPI sets.

### Procedure

For every NR trial, before building the Statistical Analysis Excel, extract the causal
chain from the feature document as follows:

1. **Read the mechanism section** (typically Section 3 or 6 of the Nokia DN PDF):
   What does the feature change at the radio/scheduling/hardware level?

2. **Classify KPIs into four categories:**

   | Category | Definition | Chart position |
   |---|---|---|
   | Primary mechanism indicators | KPIs that directly reflect the feature's operation | First |
   | Expected outcome KPIs | KPIs that change as a consequence (may be negative but bounded) | Second |
   | Watchdog KPIs | KPIs that must NOT degrade; degradation = feature is causing harm | Third |
   | Traffic context | KPIs needed to detect confounders (traffic load, active UE count) | Last |

3. **Map each KPI to a column name** from `references/nr/kpi_column_map.md`.
   Verify the column exists in the actual data file before finalising the list.

4. **Separate carrier-stratified vs cluster-level:**
   - KPIs from the main system program export → carrier-stratified (4 lines per chart)
   - KPIs from the ES cluster report → cluster-level (single brown line per chart)

### Feature mechanism disambiguation

Different Nokia feature classes have completely different causal chains. Do not
carry over a T1_KPIS list from one trial class to another:

| Feature class | Primary mechanism KPI | Expected throughput | Energy source |
|---|---|---|---|
| µDTX / Enhanced DTX | PDSCH Slot Usage ↓ | MAC Tput DL ↓ (bounded) | ES report (PA micro-sleep) |
| MIMO sleep / antenna muting | DL Rank ↓, Tx antenna usage ↓ | MAC Tput DL ↓ (bounded) | ES report (antenna shutdown) |
| Beamforming optimisation | Beam index change, SINR ↑ | MAC Tput DL ↑ | No direct ES linkage |
| DTX scheduler (legacy) | DRX Sleep Ratio ↑ | No expected throughput change | ES report |

If the feature document is ambiguous about the mechanism, state the ambiguity and ask
the user to confirm before building the causal chain. Do not assume.

### Example causal chain — µDTX feature class

```
Mechanism: consolidate DL PDSCH slots in time → longer gaps between bursts → PA can enter micro-sleep

Primary mechanism indicators:
  - PDSCH Slot Usage (%) ↓          [slot consolidation direct measure]
  - ReducedTX Power Saving Ratio (%) ↑  [PA sleep engagement]
  - DRX Sleep Ratio (%) — context

Expected outcomes:
  - Avg MAC Tput DL (Mbps) ↓        [expected per spec; bounded; not a failure]
  - Total BTS Energy (Wh) ↓         [primary success indicator — ES report]

Scheduling quality impact:
  - Avg Wideband CQI 256QAM ↓?      [monitor; slot consolidation may affect CQI reporting]
  - Avg DL Rank ↓?                  [monitor; not expected per spec but possible]

Watchdogs (must NOT degrade > 2σ):
  - PDCCH CCE Starvation Ratio ↑    [consolidation → PDCCH pressure risk]
  - QoS Flow Drop Ratio RAN ↑       [retainability]
  - SgNB Abnormal Release Ratio ↑   [SgNB retainability]

Traffic context:
  - Active DL UEs                   [confound control; must be stable across periods]
```

---

## Departure 7: BTS-Level Sanity Check (Mandatory)

### Purpose

Cluster-level KPI aggregates can mask heterogeneous behaviour across BTSs. Before
finalising the verdict, a per-BTS consistency check must be run to verify:

- The feature produced the expected primary mechanism KPI change on the majority
  of BTSs in the cluster (not just on the aggregate)
- No small subset of anomalous BTSs is dominating the cluster-level signal
- Traffic was stable across BTSs (confound control)

### When to run

Always — for every NR trial. Run after extracting statistics and before generating
the Word memo. Results populate Section 7.1 of the memo.

### Method

Using the raw main KPI file (not the cluster-level aggregate), compute per-BTS
means for baseline and trial periods for the primary causal-chain KPIs identified
in Departure 6. Then:

1. **Coverage metric:** Count and report the fraction of BTSs showing the expected
   direction of change for the primary mechanism KPI (e.g., PDSCH Slot Usage decreased).
   Report as N/total (%).

2. **Outlier detection:** For each KPI, compute a z-score for each BTS relative to
   the cluster distribution of (trial_mean − baseline_mean). Flag any BTS with
   |z| > 2.5 as an outlier. Report outlier BTS names and their values.

3. **Traffic stability:** Compute the coefficient of variation (CV) of active DL UEs
   across BTSs in both periods. If CV > 0.3, note that traffic distribution is uneven
   and may affect carrier-level aggregates.

4. **Minimum coverage threshold:** If fewer than 80% of BTSs show the expected primary
   KPI direction, the feature cannot be claimed to have operated as designed across the
   cluster — flag this in the verdict section as a condition.

### Reporting in Section 7.1

Section 7.1 must contain **quantitative findings only** — no placeholder text.
Required content:

- Total BTSs in cluster, total BTS–carrier combinations analysed
- For each primary causal-chain KPI: N/total BTSs showing expected change (%)
- Outlier BTS list with z-scores for each flagged KPI
- Traffic stability assessment
- Brief interpretation: are outliers explained by site characteristics (e.g. high-traffic
  macro sites showing lower slot consolidation gain), or do they suggest a configuration issue?

### Outlier interpretation guidance

Not all outliers are failures. Common benign explanations:

| Outlier pattern | Likely explanation | Action |
|---|---|---|
| High-traffic BTSs show lower PDSCH slot decrease | Scheduler cannot consolidate when PRBs are nearly full | Note in memo; not a feature fault |
| One or two remote BTSs flat on primary KPI | Possible configuration mismatch (parameter not applied) | Flag to user for verification |
| All outliers on same carrier | Carrier-specific scheduling issue unrelated to feature | Investigate separately |
| Random scatter of outliers, no pattern | Statistical noise from small per-BTS sample | Below significance threshold |

---

## Shared with LTE (no departure)

The following principles apply to NR unchanged — see `methodology.md`:

- Sigma convention: `sigma = (trial_mean - baseline_mean) / baseline_std_dev`
- Significance thresholds: ≥3σ critical, ≥2σ high, ≥1σ medium, <1σ noise
- Short-baseline caveat: only ≥3σ is formally "statistically significant" with 7-day
  baseline
- Near-zero variance handling: report absolute pp delta; flag sigma as "not meaningful"
- Chart sigma normalisation: positive = degradation regardless of higher_bad direction
- Verdict mapping: PASS / PASS WITH CONDITIONS / INCONCLUSIVE / FAIL / FAIL — ROLLBACK

The only verdict-level adjustment for NR: because confounders cannot be excluded from
in-cluster data alone (Departure 2), the default verdict for an otherwise clean PASS
should be **PASS WITH CONDITIONS** ("confounders not fully excluded") unless an
external control is provided. Escalate to plain PASS only if the user confirms
they have reviewed an external control separately.

---

## H0 in NR: All Carriers Activated — H1/H2 Indistinguishable

When the NR feature is a cell-level toggle applied to all NR cells simultaneously (the
most common case), there is no in-cluster unaffected carrier group. The H-framework from
`methodology.md` cannot be applied in its standard form.

**This is the H0 scenario for NR.** See `references/methodology.md` Section "H0: Band
Stratification Not Applicable" for the full procedure.

NR-specific mitigations:

1. **Carrier-only stratification still applies** — all carriers are feature bands, but
   reporting per-carrier still reveals carrier-specific behaviour.

2. **Pre-trial baseline trend check** — Plot the 7-day baseline for primary mechanism KPIs
   per carrier. If the baseline itself shows a steady improvement trend, the trial's
   improvement may be its continuation. A flat baseline + trial improvement is stronger
   H1 support.

3. **BTS sanity check (Section 7.1)** — ≥ 80% of BTSs showing the expected primary KPI
   direction provides within-cluster evidence that supports H1 over H2. A concurrent
   network event would not consistently affect 80%+ of BTSs in the same direction.

4. **Verdict**: Default PASS WITH CONDITIONS. Upgrade to PASS only when user confirms
   an external reference cluster was reviewed with no coincident trend.
