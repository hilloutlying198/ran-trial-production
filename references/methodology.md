# Analytical Methodology Reference

This document captures the analytical principles for RAN optimisation trial analysis.
Apply these consistently across all trials produced with this skill.

---

## Band Stratification (Mandatory)

Every trial must separate **Feature Bands** from **Unaffected Bands** in all KPI analysis.

| Role | Definition | Purpose in Analysis |
|------|-----------|---------------------|
| Feature Bands | Bands where the parameter was actually changed | Primary evidence for feature attribution |
| Unaffected Bands | Bands present in the cluster where parameter was NOT changed | Confounding signal detector |

**Why this matters**: If a KPI degrades on both feature and unaffected bands, the cause is
likely a concurrent network event, not the feature under test. Attributing unaffected-band
degradation to the trial feature is a category error.

**Reporting rule**: Every KPI table must have separate rows (or sub-columns) for Feature Band
aggregate and Unaffected Band aggregate. Label them clearly. Use ▲ for feature bands and
● for unaffected bands in legends.

---

## Sigma Significance Convention

Sigma (σ) measures how many standard deviations the trial period mean is from the baseline mean.

```
sigma = (trial_mean - baseline_mean) / baseline_std_dev
```

### Significance thresholds

| |σ| level | Label | Interpretation with 7-day baseline |
|-----------|-------|-------------------------------------|
| ≥ 3σ | CRITICAL | Very unlikely to be noise; warrants investigation |
| ≥ 2σ | HIGH | Statistically notable; directionally strong |
| ≥ 1σ | MEDIUM | Directional signal; treat as hypothesis, not conclusion |
| < 1σ | Noise | Within normal baseline fluctuation |

**Important caveat on short baselines**: With only 7 days of baseline, the standard deviation
estimate is itself uncertain. Treat 1–2σ findings as directional only. Only ≥ 3σ should be
called "statistically significant" in the formal report.

### Near-zero variance edge case

If a KPI was essentially constant during the baseline (std dev ≈ 0), sigma explodes to
unrealistically large values from any small absolute change. This is a statistical artefact,
not a real signal.

**Handling**: Flag these KPIs in the report legend with: "σ not meaningful — baseline variance
≈ 0; absolute pp delta is the operative metric." Report the absolute delta instead. Do not
suppress the row or set sigma to 0 — that would hide the flag.

Example: RRC SR = 100.0% baseline with std dev 0.001% → even a 0.1pp change gives σ = 100.
The absolute delta (0.1pp) is what matters, not the sigma.

---

## Chart Sigma Normalisation

In all charts, sigma must be normalised so that **positive = degradation** for every KPI,
regardless of whether "higher is better" or "lower is better."

```python
def calc_deg_sigma(sigma, higher_bad):
    """Returns sigma normalised so positive = degradation."""
    if sigma is None:
        return 0
    return sigma if higher_bad else -sigma
```

KPIs where `higher_bad = True` (raw degradation = positive sigma):
- ERAB Retain. Fail, E-RAB Drop Ratio, UL rBLER, DL rBLER, E2E Latency,
  QCI8 DL Delay, Ping RTT, HO Failure, PHO Failure

KPIs where `higher_bad = False` (raw degradation = negative sigma — must be inverted):
- RRC SR, ERAB Initial Acc, ERAB Add Acc, HO Success, PHO Success,
  DL Throughput/UE, UL Throughput/UE, DRX Sleep, PSM Ratio, ReducedTX,
  Cell Availability

**Never report raw sigma in charts without applying this normalisation.** A positive bar in
a sigma chart must always mean "this KPI got worse."

---

## H-Hypothesis Framework for Retainability

When retainability degrades, apply this decision tree before attributing to the feature:

```
Is retainability degraded on FEATURE bands?
├── No  → Feature did not cause retainability degradation. (Done)
└── Yes → Is retainability also degraded on UNAFFECTED bands?
           ├── No  → H1: Feature-induced degradation (most likely cause)
           └── Yes → Is the unaffected-band sigma comparable to feature-band sigma?
                     ├── Yes (within ~1σ) → H2: Concurrent network trend
                     │                       (coincident with trial, not caused by it)
                     └── One RC only     → H3: SW-version-specific interaction
                                           (specific to one RC's SW, not the feature)
```

### Hypothesis labels for the report

| Hypothesis | Label | Meaning |
|-----------|-------|---------|
| H1 | Feature-induced | Both feature and unaffected bands stable; feature band degrades |
| H2 | Concurrent network trend | Degradation on both band groups; likely external cause |
| H3 | RC-specific SW interaction | Only one RC's unaffected bands degrade; SW version issue |

In Section 4.3 of the report, present all three hypotheses explicitly and state which one
the data supports, with the sigma values as evidence. Do not assert H1 if the data supports H2.

---

## Attributing Events to Correct Cause

**Rule**: An event on UNAFFECTED bands cannot be attributed to the feature under test.

Before attributing any KPI movement to the feature, verify: "Was the parameter actually
changed on this band/carrier?" If the answer is no, the event requires a separate explanation.

---

## QCI Stratification

When the cluster carries multiple QCI classes, analyse primary data bearers separately:

- **QCI1 (VoLTE)**: Latency-sensitive; report E2E Latency, Ping RTT, BLER separately
- **QCI8 (default bearer / mobile broadband)**: Throughput-sensitive; report DL/UL throughput,
  BLER, E-RAB delay separately

Traffic-weighted averages across QCIs can obscure behaviour on the dominant bearer.
Always report QCI8 and QCI1 separately if data is available. State which QCI you are
reporting when giving absolute KPI values.

---

## Two-RC Trial Structure

When the trial includes two software releases (e.g., RC3 and RC4):

- Analyse each RC independently first — do not average them
- RC comparisons are only valid if baseline traffic load was similar (check PRB utilization)
- A finding that appears in both RCs provides stronger evidence than one that appears in only one
- When results diverge between RCs, state the divergence explicitly and do not force a unified
  conclusion — instead explain what the divergence implies (e.g., RC-specific SW behaviour)

---

## Verdict Mapping

Use these criteria when setting the verdict in Section 6:

| Verdict | Criteria |
|---------|----------|
| PASS | Primary KPIs improved ≥ 2σ on feature bands; watchdog KPIs ≤ 1σ degradation; confounders excluded |
| PASS WITH CONDITIONS | Primary KPIs improved but with caveats (minor secondary degradation, short baseline, confounders not fully excluded) |
| INCONCLUSIVE | Changes within 1σ on primary KPIs, or confounders cannot be distinguished from feature effect |
| FAIL | Primary KPIs show no improvement or watchdog KPIs degrade > 2σ on feature bands |
| FAIL — ROLLBACK RECOMMENDED | Clear degradation ≥ 3σ on critical KPIs with no alternative explanation |

The verdict applies to the feature as a whole across both RCs. If the RCs diverge
substantially, use INCONCLUSIVE and document the divergence.

---

## H0: Band Stratification Not Applicable

When no same-technology unaffected bands exist in the cluster, the standard H-framework
cannot be applied. This is the **H0 scenario**.

### When H0 applies

1. **LTE — all FDD bands affected**: The parameter applies to ALL FDD EARFCNs in the cluster.
   TDD carriers (e.g. B2300) are NOT a valid control — FDD and TDD differ in scheduling,
   interference patterns and load distribution. Using TDD introduces technology-mode bias.

2. **NR — feature on all carriers**: Feature is a cell-level toggle applied simultaneously to
   all NR cells. No NR carrier in the cluster remains unaffected.

### What to do under H0

1. **Document explicitly** in Section 4.3: "Band Stratification Not Applicable — [reason]."
   Do not silently omit the H-framework.

2. **Baseline-only comparison**: Compare trial-period mean vs baseline-period mean for feature
   bands. Verify the baseline was itself stable (flat daily trend).

3. **External reference cluster** (strongest mitigation): A nearby cluster that did NOT activate
   the feature. Flat external + improving trial cluster = strong H1 evidence.

4. **Verdict under H0**:
   - Default: **PASS WITH CONDITIONS** — concurrent confounders cannot be excluded from cluster
     data alone.
   - Upgrade to **PASS**: only when user confirms external reference reviewed with no coincident
     trend, OR consistent results across multiple independent clusters.

---

## Multi-Phase Trials

Some trials introduce parameter changes in sequential phases. Analyse each phase independently.

### Data structure

Nokia system program exports typically cover the entire trial window in a single file.
Phase boundaries are defined by date ranges; scripts slice the data accordingly.
Separate per-phase exports are also supported — treat each as an independent file.

### Phase labelling

| Phase | Description |
|-------|-------------|
| Baseline | Pre-activation reference period (T0 → T1) |
| Phase 1 | First parameter change applied (T1 → T2) |
| Phase N | Nth cumulative or replacement change |
| Post-RB | Optional rollback period |

### Analysis rules

1. **Phase N vs Phase N−1** — not Phase N vs Baseline, unless showing cumulative total effect.
2. **All phase boundaries shown on KPI charts** — vertical shading or dashed lines at each
   transition date. Consistent colour scheme: Baseline=grey, Ph1=blue, Ph2=teal, Post-RB=amber.
3. **Statistical Analysis Excel** — one sigma column per phase comparison (σ_Ph1, σ_Ph2 …).
4. **Technical Memo** — one subsection per phase within each KPI section (4.1–4.5).
5. **Overall verdict** applies to the final activated state vs Baseline. Intermediate phases
   showing transient effects do not independently trigger a FAIL verdict.
6. **Trial intake form** — `trial_periods.phases` array: each entry has `label`, `start`,
   `end`, `changes_applied`.
