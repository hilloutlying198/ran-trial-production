"""
extract_stats.py (NR/5G NSA) — RAN Trial Statistics Extractor for 5G NSA
==========================================================================
Reads Nokia 5G System Program KPI export(s) and (optionally) the ES cluster
energy report, computes statistical values needed by `build_stats_report_nr.py`
and `trial_memo_nr.js`.

Differences vs LTE variant (scripts/lte/extract_stats.py):
  - Uses NRARFCN (not EARFCN) as the carrier key
  - NO Feature/Unaffected band split — NR stratification is carrier-only
  - Optional --es-file for cluster-level energy KPIs (merged separately)
  - Single-RC by default; --rc2-file supported for multi-build trials

USAGE:
    python3 extract_stats.py \\
        --kpi-file /path/to/5G_System_Program_*_cluster_per_carrier.xlsx \\
        --es-file  /path/to/ES_report_*_per_cluster.xlsx \\
        --baseline-start 2026-03-23 --baseline-end 2026-03-29 \\
        --trial-start    2026-03-30 --trial-end    2026-04-16 \\
        --carriers N28,N78_F1,N78_F2,N78_F3 \\
        --trial-id CBXXXXXX --out-dir /tmp/CBXXXXXX

    Optional:
        --rc2-file path        Second Nokia KPI export for a different RC build
        --rc1-label RC1        Label for rc1 (default: "RC1")
        --rc2-label RC2        Label for rc2 (default: "RC2")
        --post-rb-start / --post-rb-end   If a post-rollback period exists

OUTPUT:
    - Prints Python code (NR_RC1_FEAT, NR_PC_RC1 arrays) for build_stats_report_nr.py
    - Writes a summary CSV for review
    - If --es-file given, writes a separate nr_es_stats.csv with cluster-level energy
      aggregates

IMPORTANT:
    - The 5G_carriers_arfcn.xlsx column labelled `EARFCN` contains NR-ARFCNs.
      This script expects `NRARFCN` in the KPI export itself; the ARFCN-to-band
      map lives in the CARRIER_MAP dict below, not in the source file.
    - On first run with real ES data, the NR_ES_COLUMN_MAP below will likely not
      match your ES report's actual columns. Edit this file to add the real names
      OR pass them via CLI flags (future work).
"""

import warnings; warnings.filterwarnings('ignore')
import argparse, re, sys, json
from pathlib import Path
import pandas as pd
import numpy as np

# ─── NR-ARFCN → carrier label map ─────────────────────────────────────────────────
# Update this map with your cluster's actual NRARFCNs. Keep in sync with
# references/nr/carrier_allocation.md
MNO_NR_NRARFCN_MAP = {
    152600: 'N28',
    635334: 'N78_F1',
    650666: 'N78_F2',
    652000: 'N78_F3',
}

# Carrier → band group (for aggregate-by-band-group analysis if requested)
MNO_NR_BAND_GROUP = {
    'N28':    'n28',
    'N78_F1': 'n78',
    'N78_F2': 'n78',
    'N78_F3': 'n78',
}

CARRIER_DISPLAY_ORDER = ['N28', 'N78_F1', 'N78_F2', 'N78_F3']

# ─── Nokia NR source column → display name, tier, higher_bad flag ────────────
# Authoritative source: references/nr/kpi_column_map.md
# This map is the subset of 132 NR columns that are reported in stats Excel + memo.
# EXCL columns (100% NaN in reference data) are commented out but retained for
# other-cluster reuse; extract_stats will auto-drop any column whose data is empty.
NR_COLUMN_MAP = {
    # T1-ES (Primary — Energy Saving)
    'Cell in Reduced TX Power Saving Mode Ratio':                     ('ReducedTX Ratio',       'T1-ES',   False),
    'DRX sleep time ratio':                                           ('DRX Sleep Ratio',       'T1-ES',   False),
    'Usage ratio of PDSCH data slots over all DL data slots':         ('PDSCH Slot Usage',      'T1-ES',   False),

    # T1-Lat (Primary — Latency) — PDF expected-impact
    'Average delay DL in CU_UP per cell':                             ('Avg DL Delay CU-UP',    'T1-Lat',  True),

    # T1-Tput (Primary — Throughput) — PDF expected-impact
    'Average MAC layer user throughput in downlink':                  ('Avg MAC Tput DL',       'T1-Tput', False),

    # T2 (Secondary / correlated)
    'Average PDCP re_ordering delay in the UL per cell':              ('Avg UL Reorder Delay',  'T2',      True),
    'Average wideband CQI 64QAM table':                               ('Avg CQI 64QAM',         'T2',      False),
    'Average wideband CQI 256QAM table':                              ('Avg CQI 256QAM',        'T2',      False),
    'Average UE related SINR for PUSCH in Rank 1':                    ('Avg SINR PUSCH R1',     'T2',      False),
    'Average UE related SINR for PUSCH in Rank 2':                    ('Avg SINR PUSCH R2',     'T2',      False),
    'Average UE related SINR for PUCCH':                              ('Avg SINR PUCCH',        'T2',      False),
    'Average UE power headroom for PUSCH calculated from histogram counters': ('Avg PHR PUSCH', 'T2',      False),
    'Average UE pathloss level for PUSCH':                            ('Avg Pathloss PUSCH',    'T2',      True),
    'Maximum DL PDCP SDU NR leg throughput per DRB':                  ('Max DL PDCP Tput',      'T2',      False),
    'Maximum MAC SDU Cell Throughput in DL on DTCH':                  ('Max Cell Tput DL',      'T2',      False),
    'Maximum MAC SDU Cell Throughput in UL on DTCH':                  ('Max Cell Tput UL',      'T2',      False),
    'Average MCS used in downlink for PDSCH with 64QAM table':        ('Avg MCS DL 64QAM',      'T2',      False),
    'Average MCS used in downlink for PDSCH with 256QAM table':       ('Avg MCS DL 256QAM',     'T2',      False),
    'Average rank used in downlink':                                  ('Avg DL Rank',           'T2',      False),
    'Average MCS used in uplink for PUSCH with 64QAM table':          ('Avg MCS UL 64QAM',      'T2',      False),
    'PRB utilization for PDSCH':                                      ('PRB Util DL',           'T2',      False),
    'PRB utilization for PUSCH':                                      ('PRB Util UL',           'T2',      False),
    'Usage ratio of PUSCH data slots over all UL data slots':         ('PUSCH Slot Usage',      'T2',      False),
    'Average aggregation level used on PDCCH uplink grants':          ('Avg PDCCH AGG UL',      'T2',      False),
    'Average aggregation level used on PDCCH downlink grants':        ('Avg PDCCH AGG DL',      'T2',      False),
    'Admission control rejection ratio due to lack of PUCCH resources':   ('PUCCH Rej NSA',     'T2',      True),
    'Admission control rejection ratio due to lack of PUCCH resources.1': ('PUCCH Rej SA',      'T2',      True),

    # T3 (Watchdog — must not degrade)
    'Cell availability ratio':                                        ('Cell Availability',     'T3',      False),
    'Cell availability ratio excluding planned unavailability periods': ('Cell Avail (excl)',   'T3',      False),
    'Accessibility success ratio':                                    ('Accessibility SR',      'T3',      False),
    'Initial UE message sent success ratio':                          ('Init UE Msg SR',        'T3',      False),
    'NGAP connection establishment success ratio':                    ('NGAP Setup SR',         'T3',      False),
    'QoS Flow Setup Success Ratio':                                   ('QoS Flow Setup SR',     'T3',      False),
    'Non_Stand Alone call accessibility 5G side':                     ('NSA Call Access SR',    'T3',      False),
    'RRC connection establishment success ratio':                     ('RRC Setup SR',          'T3',      False),
    'Initial E_RAB Setup Success Ratio':                              ('Init E-RAB SR',         'T3',      False),
    'UE context setup success ratio':                                 ('UE Ctx Setup SR',       'T3',      False),
    'Radio admission success ratio for NSA user':                     ('Radio Admission NSA',   'T3',      False),
    'Radio admission success ratio for SA users':                     ('Radio Admission SA',    'T3',      False),
    'Active RACH setup success ratio':                                ('Active RACH SR',        'T3',      False),
    'Contention based RACH setup success ratio':                      ('CB RACH SR',            'T3',      False),
    'Contention free RACH setup success ratio':                       ('CF RACH SR',            'T3',      False),
    'SgNB addition preparation success ratio':                        ('SgNB Add Prep SR',      'T3',      False),
    'SgNB reconfiguration success ratio':                             ('SgNB Reconfig SR',      'T3',      False),
    'Status Transfer failure ratio during SgNB Addition':             ('SgNB Xfer Fail',        'T3',      True),
    'QoS Flow Drop Ratio _ RAN view':                                 ('QoS Flow Drop RAN',     'T3',      True),
    'QoS Flow Drop Ratio _ User view_double_Ng mapped to UE lost':    ('QoS Flow Drop UEL',     'T3',      True),
    'Active QoS Flow Drop Ratio_double_Ng mapped to UE lost':         ('Active QoS Drop',       'T3',      True),
    'Active E_RAB Drop Ratio _ SgNB view':                            ('Active E-RAB Drop',     'T3',      True),
    'SgNB triggered abnormal release ratio excluding X2 reset':       ('SgNB Abn Release',      'T3',      True),
    'Ratio of SgNB releases initiated by SgNB due to radio connection with UE lost': ('SgNB Rel UEL', 'T3', True),
    'Ratio of UE releases due to abnormal reasons':                   ('UE Abn Release',        'T3',      True),
    'Number of UE releases due to radio link failure':                ('RLF UE Rel',            'T3',      True),
    'Number of UE redirections to E_UTRAN due to voice fallback to LTE': ('EPS Fallback',       'T3',      True),
    'Intra_frequency Intra_gNB Intra_DU handover total success ratio':  ('Intra-DU IF HO SR',   'T3',      False),
    'Intra_gNB Intra_DU Inter_frequency HO total success ratio per PLMN': ('Intra-DU XF HO SR', 'T3',      False),
    'Intra_frequency Xn based Inter_gNB handover execution success ratio per PLMN': ('Xn Inter-gNB HO SR', 'T3', False),
    'Xn based Inter_gNB Inter_frequency HO execution success ratio per PLMN': ('Xn Inter-gNB XF HO SR', 'T3', False),
    'Inter gNB handover success ratio for NSA':                       ('Inter-gNB HO NSA',      'T3',      False),
    'Inter_frequency intra_DU handover total success ratio for NSA':  ('XF Intra-DU HO NSA',    'T3',      False),
    'Intra_frequency intra_DU PSCell change preparation success ratio': ('PSCell Chg Prep SR', 'T3',       False),
    'Intra_frequency intra_DU PSCell change total success ratio':     ('PSCell Chg SR',         'T3',      False),
    'Downlink carrier aggregation reconfiguration success ratio':     ('DL CA Reconfig SR',     'T3',      False),
    'Average PDCCH CCE starvation ratio in cell':                     ('PDCCH Starvation',      'T3',      True),   # PDF watchdog

    # T4-Traffic (Context only — not ranked for significance)
    'Average number of active UEs with data in the buffer for DRBs in DL':    ('Avg Active DL UEs', 'T4-Traffic', False),
    'Average number of active UEs with data in the buffer for DRBs in UL':    ('Avg Active UL UEs', 'T4-Traffic', False),
    'Average number of NSA users in selected area':                   ('Avg NSA Users',         'T4-Traffic', False),
    'Average number of SA RRC connected users in selected area':      ('Avg SA RRC Users',      'T4-Traffic', False),
    'MAC SDU data volume transmitted in DL on DTCH':                  ('DL Data Volume',        'T4-Traffic', False),
    'MAC SDU data volume received in UL on DTCH':                     ('UL Data Volume',        'T4-Traffic', False),
}

# ─── ES (Energy Saving) column map — PLACEHOLDERS ────────────────────────────
# These are placeholders. On first real run with the ES cluster report, inspect
# the export and fix these to real column names. Until then, --es-file passes
# are best-effort.
NR_ES_COLUMN_MAP = {
    # Cluster-level energy KPIs from ES_report_*_per_cluster.xlsx
    # Units: raw Nokia counters (likely mJ for energy, mW for power — verify with vendor).
    # higher_bad=True for consumption (less is better); False for saving indicators.
    '[N]RU_ENERGY_CONSUMPTION':        ('RU Energy Consumption',  'T1-ES', True),
    '[N]RU_AVG_PWR_USAGE':             ('RU Avg Power Usage',     'T1-ES', True),
    '[N]RU_MAX_PWR_USAGE':             ('RU Max Power Usage',     'T2',    True),
    '[N]RU_MIN_PWR_USAGE':             ('RU Min Power Usage',     'T2',    True),
    '[N]ENERGY_CONSUMPTION_IN_SM':     ('System Module Energy',   'T1-ES', True),
    '[N]ENERGY_CONSUMPTION_IN_RF':     ('RF Energy',              'T1-ES', True),
    '[N]ENERGY_CONSUMPTION_IN_BTS':    ('Total BTS Energy',       'T1-ES', True),
    '[N]MAX_INPUT_VOLTAGE_IN_RF':      ('Max RF Input Voltage',   'T4-Traffic', False),
}

# Per-carrier KPI subset (shown in the Per_Carrier_Detail sheet)
PER_CARRIER_KPIS_MAP = {
    'Cell in Reduced TX Power Saving Mode Ratio':               'ReducedTX Ratio',
    'DRX sleep time ratio':                                     'DRX Sleep',
    'Usage ratio of PDSCH data slots over all DL data slots':   'PDSCH Slot Usage',
    'Average delay DL in CU_UP per cell':                       'Avg DL Delay',
    'Average MAC layer user throughput in downlink':            'Avg MAC Tput DL',
    'Average PDCCH CCE starvation ratio in cell':               'PDCCH Starvation',
}

# Ratio-like KPIs aggregate as MEAN; counter-like KPIs aggregate as SUM
MEAN_KW = ['ratio','rate','success','efficiency','average','avg ','cqi','sinr','rssi','bler',
           'mcs','percentage','maximum','peak','latency','delay','distribution','starvation',
           'usage','level','headroom','sleep','reduced','availability','pathloss',
           'retainability','accessibility','admission','fallback','utilization','utilisation',
           'aggregation','holding','drop','abnormal','release']

SUM_KW = ['number of','attempts','data volume','requests','releases','redirections']


def is_mean(col: str) -> bool:
    """Return True if the column should aggregate as MEAN, False for SUM."""
    low = col.lower()
    # SUM keywords take priority (more specific)
    for kw in SUM_KW:
        if kw in low:
            return False
    for kw in MEAN_KW:
        if kw in low:
            return True
    # Default: MEAN for unknowns (safer — it won't inflate the daily value by summing)
    return True


# ─── Loader: NR KPI export ───────────────────────────────────────────────────
def load_nr_kpi_export(path: str, nrarfcn_map: dict  # pass MNO_NR_NRARFCN_MAP) -> pd.DataFrame:
    """Load Nokia 5G system program export. Filter to MNO carriers. Add CARRIER + BAND_GROUP."""
    df = pd.read_excel(path, engine='openpyxl')
    df.columns = df.columns.str.strip()

    # DATETIME column
    dt_col = next((c for c in df.columns if c.upper() in ('DATETIME', 'DATE', 'PERIOD START TIME')), None)
    if dt_col is None:
        dt_col = df.columns[0]
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')
    df = df.dropna(subset=['DATETIME'])

    # NRARFCN column
    nr_col = next((c for c in df.columns if 'NRARFCN' in c.upper()), None)
    if nr_col is None:
        raise ValueError(f"No NRARFCN column found in {path}. First 10 cols: {list(df.columns[:10])}")
    df['NRARFCN'] = pd.to_numeric(df[nr_col], errors='coerce')

    # Filter + label
    df = df[df['NRARFCN'].isin(nrarfcn_map)].copy()
    df['CARRIER'] = df['NRARFCN'].map(nrarfcn_map)
    df['BAND_GROUP'] = df['CARRIER'].map(MNO_NR_BAND_GROUP)

    if df.empty:
        raise ValueError(f"No rows match NRARFCN filter in {path}. Check MNO_NR_NRARFCN_MAP.")

    return df


# ─── Loader: ES cluster report ───────────────────────────────────────────────
def load_nr_es_report(path: str) -> pd.DataFrame:
    """Load ES cluster report. No per-carrier; just datetime + counters."""
    df = pd.read_excel(path, engine='openpyxl')
    df.columns = df.columns.str.strip()

    dt_col = next((c for c in df.columns if c.upper() in ('DATETIME', 'DATE', 'PERIOD START TIME')), None)
    if dt_col is None:
        dt_col = df.columns[0]
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')
    df = df.dropna(subset=['DATETIME'])

    return df


# ─── Core stats computation ──────────────────────────────────────────────────
def compute_period_stats(df: pd.DataFrame, kpi_cols: list,
                         baseline_mask, trial_mask, post_rb_mask=None) -> list:
    """
    Compute per-KPI stats across a DataFrame that has already been restricted to a
    carrier subset (or the entire cluster for ES data).

    Returns list of dicts with: col, bl (mean), tr (mean), pr (mean or None),
    sigma (or None), bl_std.
    """
    rows = []
    for c in kpi_cols:
        if c not in df.columns:
            continue
        try:
            agg_func = 'mean' if is_mean(c) else 'sum'
            # Daily aggregate across carriers (or just pass-through for single-carrier/cluster data)
            bl_daily = df[baseline_mask].groupby('DATETIME')[c].agg(agg_func).dropna()
            tr_daily = df[trial_mask].groupby('DATETIME')[c].agg(agg_func).dropna()

            if len(bl_daily) == 0 or len(tr_daily) == 0:
                continue

            bl_mean = float(bl_daily.mean())
            bl_std  = float(bl_daily.std(ddof=1)) if len(bl_daily) > 1 else None
            tr_mean = float(tr_daily.mean())

            pr_mean = None
            if post_rb_mask is not None:
                pr_daily = df[post_rb_mask].groupby('DATETIME')[c].agg(agg_func).dropna()
                if len(pr_daily):
                    pr_mean = float(pr_daily.mean())

            sigma = None
            if bl_std and bl_std > 1e-9:
                sigma = round((tr_mean - bl_mean) / bl_std, 2)

            rows.append({
                'col': c,
                'bl': round(bl_mean, 4),
                'tr': round(tr_mean, 4),
                'pr': round(pr_mean, 4) if pr_mean is not None else None,
                'sigma': sigma,
                'bl_std': round(bl_std, 4) if bl_std else None,
                'n_bl': len(bl_daily),
                'n_tr': len(tr_daily),
            })
        except Exception as e:
            print(f"  [warn] {c}: {e}", file=sys.stderr)
    return rows


def compute_per_carrier_stats(df: pd.DataFrame, kpi_cols: list,
                               carriers: list,
                               baseline_mask, trial_mask) -> dict:
    """For the subset KPIs, compute baseline/trial mean per carrier."""
    out = {}
    for carrier in carriers:
        cdf = df[df['CARRIER'] == carrier]
        if cdf.empty:
            continue
        bm = baseline_mask & (df['CARRIER'] == carrier)
        tm = trial_mask & (df['CARRIER'] == carrier)
        stats = compute_period_stats(df, kpi_cols, bm, tm, None)
        out[carrier] = {r['col']: (r['bl'], r['tr'], r['sigma']) for r in stats}
    return out


# ─── Output formatting ───────────────────────────────────────────────────────
def format_nr_feat_array(stats_rows: list, label: str, col_map: dict) -> str:
    """Format NR_RC1_FEAT (or equivalent) as a Python array for pasting into report script."""
    lines = [f"{label} = ["]
    lines.append(f"  # (display_name, tier, higher_bad, baseline, trial, post_rb_or_None, sigma_or_None)")
    for r in stats_rows:
        col = r['col']
        if col not in col_map:
            continue
        name, tier, hib = col_map[col]
        pr_str = f"{r['pr']}" if r['pr'] is not None else 'None'
        sig_str = f"{r['sigma']}" if r['sigma'] is not None else 'None'
        lines.append(
            f"  ({name!r:<24}, {tier!r:<10}, {str(hib):<5}, "
            f"{r['bl']}, {r['tr']}, {pr_str}, {sig_str}),"
        )
    lines.append("]")
    return "\n".join(lines)


def format_per_carrier_dict(pc_data: dict, label: str, col_map: dict) -> str:
    """Format NR_PC_RC1 = { 'N28': {kpi: (bl,tr,sigma)}, ... }"""
    lines = [f"{label} = {{"]
    for carrier, kpis in pc_data.items():
        lines.append(f"    {carrier!r}: {{")
        for col, (bl, tr, sigma) in kpis.items():
            if col not in col_map:
                continue
            disp = col_map[col][0]
            sig_str = str(sigma) if sigma is not None else 'None'
            lines.append(f"        {disp!r:<22}: ({bl}, {tr}, {sig_str}),")
        lines.append("    },")
    lines.append("}")
    return "\n".join(lines)


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="NR (5G NSA) stats extractor for ran-trial-production")
    ap.add_argument('--kpi-file', required=True, help='Nokia 5G System Program cluster-per-carrier export')
    ap.add_argument('--rc2-file', default=None, help='Optional second Nokia export (different RC build)')
    ap.add_argument('--es-file',  default=None, help='Optional ES cluster report for energy KPIs')
    ap.add_argument('--baseline-start', required=True)
    ap.add_argument('--baseline-end',   required=True)
    ap.add_argument('--trial-start',    required=True)
    ap.add_argument('--trial-end',      required=True)
    ap.add_argument('--post-rb-start', default=None)
    ap.add_argument('--post-rb-end',   default=None)
    ap.add_argument('--carriers', default=','.join(CARRIER_DISPLAY_ORDER),
                    help=f'Comma-separated carrier labels (default: {",".join(CARRIER_DISPLAY_ORDER)})')
    ap.add_argument('--rc1-label', default='RC1')
    ap.add_argument('--rc2-label', default='RC2')
    ap.add_argument('--trial-id', default='NR_TRIAL')
    ap.add_argument('--out-dir',  default='/tmp/nr_trial')
    args = ap.parse_args()

    carriers = [c.strip() for c in args.carriers.split(',') if c.strip()]
    out_dir = Path(args.out_dir); out_dir.mkdir(parents=True, exist_ok=True)

    print(f"=== NR extract_stats — trial {args.trial_id} ===", file=sys.stderr)
    print(f"Carriers: {carriers}", file=sys.stderr)
    print(f"Baseline: {args.baseline_start} → {args.baseline_end}", file=sys.stderr)
    print(f"Trial:    {args.trial_start} → {args.trial_end}", file=sys.stderr)
    if args.post_rb_start:
        print(f"Post-RB:  {args.post_rb_start} → {args.post_rb_end}", file=sys.stderr)

    # --- RC1 ---
    df1 = load_nr_kpi_export(args.kpi_file, MNO_NR_NRARFCN_MAP)
    df1 = df1[df1['CARRIER'].isin(carriers)]
    print(f"\n[{args.rc1_label}] loaded: {len(df1)} rows, "
          f"{df1['CARRIER'].nunique()} carriers, "
          f"dates {df1['DATETIME'].min().date()} → {df1['DATETIME'].max().date()}", file=sys.stderr)

    # Period masks
    bl_mask = (df1['DATETIME'] >= args.baseline_start) & (df1['DATETIME'] <= args.baseline_end)
    tr_mask = (df1['DATETIME'] >= args.trial_start)    & (df1['DATETIME'] <= args.trial_end)
    pr_mask = None
    if args.post_rb_start:
        pr_mask = (df1['DATETIME'] >= args.post_rb_start) & (df1['DATETIME'] <= args.post_rb_end)

    # Identify kept KPI columns (present in map AND in the export)
    kpi_cols = [c for c in NR_COLUMN_MAP if c in df1.columns]
    dropped = [c for c in NR_COLUMN_MAP if c not in df1.columns]
    if dropped:
        print(f"[{args.rc1_label}] Columns in map but not in export ({len(dropped)}):",
              file=sys.stderr)
        for c in dropped: print(f"    - {c}", file=sys.stderr)

    # All-carriers cluster-level stats
    stats1 = compute_period_stats(df1, kpi_cols, bl_mask, tr_mask, pr_mask)
    # Per-carrier stats for a subset
    pc_cols = [c for c in PER_CARRIER_KPIS_MAP if c in df1.columns]
    pc1 = compute_per_carrier_stats(df1, pc_cols, carriers, bl_mask, tr_mask)

    # --- Print Python arrays ready to paste into build_stats_report_nr.py ---
    print("\n# ======================================================================")
    print("# === Paste this block into scripts/nr/build_stats_report_nr.py ==========")
    print("# ======================================================================\n")
    print(format_nr_feat_array(stats1, f"NR_{args.rc1_label}_FEAT", NR_COLUMN_MAP))
    print()
    print(format_per_carrier_dict(pc1, f"NR_PC_{args.rc1_label}", NR_COLUMN_MAP))

    # --- Save a CSV summary ---
    summary_rows = []
    for r in stats1:
        name, tier, hib = NR_COLUMN_MAP.get(r['col'], (r['col'], '?', '?'))
        summary_rows.append({
            'KPI': name, 'Tier': tier, 'higher_bad': hib,
            'Baseline_Mean': r['bl'], 'Trial_Mean': r['tr'], 'PostRB_Mean': r['pr'],
            'Sigma': r['sigma'], 'Baseline_Std': r['bl_std'],
            'N_Baseline_Days': r['n_bl'], 'N_Trial_Days': r['n_tr'],
        })
    summary_df = pd.DataFrame(summary_rows)
    summary_df = summary_df.sort_values(by=['Tier', 'Sigma'], ascending=[True, False], na_position='last')
    csv_path = out_dir / f'{args.trial_id}_nr_stats_{args.rc1_label}.csv'
    summary_df.to_csv(csv_path, index=False)
    print(f"\n[saved] {csv_path}", file=sys.stderr)

    # --- RC2 (if provided) ---
    if args.rc2_file:
        df2 = load_nr_kpi_export(args.rc2_file, MNO_NR_NRARFCN_MAP)
        df2 = df2[df2['CARRIER'].isin(carriers)]
        bl2 = (df2['DATETIME'] >= args.baseline_start) & (df2['DATETIME'] <= args.baseline_end)
        tr2 = (df2['DATETIME'] >= args.trial_start)    & (df2['DATETIME'] <= args.trial_end)
        pr2 = (df2['DATETIME'] >= args.post_rb_start)  & (df2['DATETIME'] <= args.post_rb_end) if args.post_rb_start else None
        kpi_cols2 = [c for c in NR_COLUMN_MAP if c in df2.columns]
        stats2 = compute_period_stats(df2, kpi_cols2, bl2, tr2, pr2)
        pc_cols2 = [c for c in PER_CARRIER_KPIS_MAP if c in df2.columns]
        pc2 = compute_per_carrier_stats(df2, pc_cols2, carriers, bl2, tr2)

        print("\n" + format_nr_feat_array(stats2, f"NR_{args.rc2_label}_FEAT", NR_COLUMN_MAP))
        print()
        print(format_per_carrier_dict(pc2, f"NR_PC_{args.rc2_label}", NR_COLUMN_MAP))

        csv2 = out_dir / f'{args.trial_id}_nr_stats_{args.rc2_label}.csv'
        pd.DataFrame([{
            'KPI': NR_COLUMN_MAP.get(r['col'], (r['col'],))[0], 'Tier': NR_COLUMN_MAP.get(r['col'], ('?','?','?'))[1],
            'Baseline_Mean': r['bl'], 'Trial_Mean': r['tr'], 'Sigma': r['sigma'],
        } for r in stats2]).to_csv(csv2, index=False)
        print(f"[saved] {csv2}", file=sys.stderr)

    # --- ES (if provided) ---
    if args.es_file:
        if not NR_ES_COLUMN_MAP:
            print("\n[!] --es-file supplied but NR_ES_COLUMN_MAP is empty — edit extract_stats.py "
                  "to add real ES column names before using.", file=sys.stderr)
        else:
            es_df = load_nr_es_report(args.es_file)
            es_bl = (es_df['DATETIME'] >= args.baseline_start) & (es_df['DATETIME'] <= args.baseline_end)
            es_tr = (es_df['DATETIME'] >= args.trial_start)    & (es_df['DATETIME'] <= args.trial_end)
            es_pr = None
            if args.post_rb_start:
                es_pr = (es_df['DATETIME'] >= args.post_rb_start) & (es_df['DATETIME'] <= args.post_rb_end)

            # ES has no CARRIER, so feed groupby with a dummy key by using DATETIME-only
            es_cols = [c for c in NR_ES_COLUMN_MAP if c in es_df.columns]
            # Reuse compute_period_stats by injecting a singleton CARRIER column
            es_df2 = es_df.copy()
            es_df2['CARRIER'] = 'CLUSTER'
            es_stats = compute_period_stats(es_df2, es_cols, es_bl, es_tr, es_pr)

            print("\n# === ES (Energy-Saving) cluster-level stats ==========================\n")
            print(format_nr_feat_array(es_stats, 'NR_ES_FEAT', NR_ES_COLUMN_MAP))

            es_csv = out_dir / f'{args.trial_id}_nr_es_stats.csv'
            pd.DataFrame([{
                'KPI': NR_ES_COLUMN_MAP.get(r['col'], (r['col'],))[0],
                'Baseline': r['bl'], 'Trial': r['tr'], 'Sigma': r['sigma'],
            } for r in es_stats]).to_csv(es_csv, index=False)
            print(f"[saved] {es_csv}", file=sys.stderr)


if __name__ == '__main__':
    main()
