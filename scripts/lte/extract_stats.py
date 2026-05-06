"""
extract_stats.py — RAN Trial Statistics Extractor
===================================================
Reads raw Nokia KPI engine Excel export(s) and computes all statistical values
needed by build_stats_report_template.py, replacing the need to fill in Sections
5, 6, and 7 of the trial intake template manually.

USAGE:
    python extract_stats.py --config /path/to/trial_intake.md

    Or with explicit arguments:
    python extract_stats.py \\
        --rc1-file /path/to/RC3_export.xlsx \\
        --rc2-file /path/to/RC4_export.xlsx \\
        --baseline-start 2026-01-28 --baseline-end 2026-02-03 \\
        --trial-start 2026-02-04 --trial-end 2026-03-02 \\
        --post-rb-start 2026-03-03 --post-rb-end 2026-03-15 \\
        --feature-bands B800,B900,B1800,B2100 \\
        --unaffected-bands B700,B2300_F1,B2300_F2 \\
        --rc1-label RC3 --rc2-label RC4

OUTPUT:
    Prints Python code (RC3_FEAT, RC4_FEAT, BAND_CMP, PC_RC3, PC_RC4 arrays)
    ready to drop into build_stats_report_template.py.
    Also writes a summary CSV for review.
"""

import warnings; warnings.filterwarnings('ignore')
import argparse, re, sys, json
from pathlib import Path
import pandas as pd
import numpy as np

# ─── Nokia EARFCN → band label map (MNO 4G cluster) ───────────────────────
# Update this if the cluster has different EARFCNs for a new network/operator.
DEFAULT_EARFCN_MAP = {
    9260:  'B700',
    6400:  'B800',
    3725:  'B900',
    1226:  'B1800',
    347:   'B2100',
    39250: 'B2300_F1',
    39448: 'B2300_F2',
}

# ─── Nokia source column → display name + higher_bad flag ─────────────────────
# Maps Nokia export column names to the short names used in the stats report.
# Extend this dict if new KPIs are added to the source file.
# Format: 'Nokia column name': ('Display name', tier, higher_bad)
COLUMN_MAP = {
    # Power Saving (T1-PS)
    'Cell in Power Saving Mode Ratio':                  ('PSM Ratio',          'T1-PS',  False),
    'Cell in Reduced TX Power Saving Mode Ratio':       ('ReducedTX Ratio',    'T1-PS',  False),
    'DRX Sleep Ratio':                                  ('DRX Sleep Ratio',    'T1-PS',  False),
    # Latency (T1-Lat)
    'Average Latency Downlink':                         ('Avg Latency DL',     'T1-Lat', True),
    'Average PDCP SDU Delay in DL QCI1':                ('SDU Delay QCI1',     'T1-Lat', True),
    'Average PDCP SDU Delay in DL QCI8':                ('SDU Delay QCI8',     'T1-Lat', True),
    'Average PDCP SDU Delay in DL QCI9':                ('SDU Delay QCI9',     'T1-Lat', True),
    # Secondary (T2)
    'Residual Block Error Rate_rBLER in UL':            ('UL rBLER',           'T2',     True),
    'Residual Block Error Rate_rBLER in DL':            ('DL rBLER',           'T2',     True),
    'Average used MCS on PUSCH transmissions':          ('Avg UL MCS',         'T2',     False),
    'DL Spectral efficiency':                           ('DL Spectral Eff',    'T2',     False),
    'Average PDCP Layer Active Cell Throughput DL':     ('Tput DL Active',     'T2',     False),
    'Average PDCP Layer Active Cell Throughput UL':     ('Tput UL Active',     'T2',     False),
    # Watchdog (T3)
    'Cell Availability Ratio':                          ('Cell Availability',  'T3',     False),
    'RACH Setup Completion Success Rate':               ('RACH SR',            'T3',     False),
    'E_RAB Setup Success Ratio':                        ('E-RAB SR',           'T3',     False),
    'Total RRC Connection Setup Success Ratio':         ('RRC SR',             'T3',     False),
    'E_RAB Drop Ratio RAN View':                        ('E-RAB Drop Ratio',   'T3',     True),
    'E_RAB Retainability Rate RAN View RNL Failure with UE Lost':
                                                        ('ERAB Retain. Fail',  'T3',     True),
    'Total HO Success Ratio intra eNB':                 ('HO Intra-eNB SR',   'T3',     False),
}

# Band comparison watchdog KPIs (must match BAND_CMP_KPIS in stats report template)
BAND_CMP_KPIS_MAP = {
    'E_RAB Retainability Rate RAN View RNL Failure with UE Lost': 'ERAB Retain. Fail',
    'Residual Block Error Rate_rBLER in UL':                      'UL rBLER',
    'E_RAB Drop Ratio RAN View':                                   'E-RAB Drop Ratio',
    'Cell Availability Ratio':                                     'Cell Availability',
    'Cell in Power Saving Mode Ratio':                            'PSM Ratio',
}

# Per-carrier KPIs for PC_RCx (Nokia col → short label)
PER_CARRIER_MAP = {
    'DRX Sleep Ratio':                      'DRX Sleep',
    'Average Latency Downlink':             'Latency DL',
    'Average PDCP SDU Delay in DL QCI8':    'QCI8 Delay',
    'Cell in Power Saving Mode Ratio':      'PSM Ratio',
    'Cell in Reduced TX Power Saving Mode Ratio': 'ReducedTX',
}

# Ratio KPIs (aggregated with MEAN, not SUM)
MEAN_KW = ['ratio','rate','efficiency','average','cqi','sinr','rssi','bler',
           'mcs','percentage','maximum','latency','delay','distribution',
           'usage','rbler','level','headroom','offset','spectral','avg ue',
           'avg level','agg level','symbol']

def is_mean(col):
    return any(k in col.lower() for k in MEAN_KW)


def load_and_filter(path, earfcn_map):
    """Load Nokia export, apply EARFCN filter, add BAND and BAND_GROUP columns."""
    df = pd.read_excel(path, engine='openpyxl')

    # Normalise column names: strip extra whitespace
    df.columns = df.columns.str.strip()

    # Find datetime column (usually first column, or named 'DATETIME' / 'Date' / 'Period')
    dt_col = None
    for c in df.columns:
        if any(k in c.lower() for k in ('datetime','date','period','time')):
            dt_col = c
            break
    if dt_col is None:
        dt_col = df.columns[0]
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce')
    df = df.dropna(subset=['DATETIME'])

    # Find EARFCN column
    earfcn_col = None
    for c in df.columns:
        if 'earfcn' in c.lower():
            earfcn_col = c
            break
    if earfcn_col is None:
        raise ValueError(f"No EARFCN column found in {path}. Columns: {list(df.columns[:10])}")

    df['EARFCN'] = pd.to_numeric(df[earfcn_col], errors='coerce')
    df = df[df['EARFCN'].isin(earfcn_map)].copy()
    df['BAND'] = df['EARFCN'].map(earfcn_map)

    if df.empty:
        raise ValueError(f"No rows match EARFCN filter in {path}. Check earfcn_map.")

    return df


def assign_band_groups(df, feature_bands, unaffected_bands):
    """Add BAND_GROUP column: 'feat' or 'unaff'."""
    def grp(band):
        if band in feature_bands:   return 'feat'
        if band in unaffected_bands: return 'unaff'
        return None
    df['BAND_GROUP'] = df['BAND'].map(grp)
    return df[df['BAND_GROUP'].notna()].copy()


def aggregate_by_period(df, period_mask, kpi_cols):
    """Compute daily aggregate across bands for rows in period_mask."""
    sub = df[period_mask].copy()
    if sub.empty:
        return pd.Series(dtype=float)

    # Aggregate per day first, then across days
    agg_rules = {c: ('mean' if is_mean(c) else 'sum') for c in kpi_cols}
    daily = sub.groupby('DATETIME').agg(agg_rules)
    # Then mean/sum across days (for ratios: mean; for counters: mean of daily sums)
    result = {}
    for c in kpi_cols:
        result[c] = daily[c].mean()
    return pd.Series(result)


def compute_stats(df, kpi_cols, baseline_mask, trial_mask, post_rb_mask):
    """Compute baseline mean/std, trial mean, post-rb mean, sigma."""
    rows = []
    for c in kpi_cols:
        try:
            bl_vals = df[baseline_mask]['DATETIME'].map(
                lambda dt: None  # placeholder
            )
            # Daily means per period
            get_daily = lambda mask, col: (
                df[mask].groupby('DATETIME')[col]
                .agg('mean' if is_mean(col) else 'sum')
            )
            bl_daily = get_daily(baseline_mask, c)
            tr_daily = get_daily(trial_mask, c)
            pr_daily = get_daily(post_rb_mask, c) if post_rb_mask is not None else pd.Series(dtype=float)

            bl_mean = bl_daily.mean()
            bl_std  = bl_daily.std(ddof=1)  # sample std
            tr_mean = tr_daily.mean()
            pr_mean = pr_daily.mean() if not pr_daily.empty else None

            if pd.isna(bl_mean) or pd.isna(tr_mean):
                continue

            sigma = None
            if bl_std and not pd.isna(bl_std) and bl_std > 1e-9:
                sigma = round((tr_mean - bl_mean) / bl_std, 1)
            # else sigma stays None (near-zero variance — flag in output)

            rows.append({
                'col': c,
                'bl': round(bl_mean, 3),
                'tr': round(tr_mean, 3),
                'pr': round(pr_mean, 3) if pr_mean is not None and not pd.isna(pr_mean) else None,
                'sigma': sigma,
                'bl_std': round(bl_std, 4) if bl_std and not pd.isna(bl_std) else None,
            })
        except Exception as e:
            print(f"  [warn] {c}: {e}", file=sys.stderr)

    return rows


def format_feat_array(stats_rows, label):
    """Format RC3_FEAT / RC4_FEAT Python array."""
    lines = [f"{label} = ["]
    for r in stats_rows:
        col = r['col']
        if col not in COLUMN_MAP:
            continue
        name, tier, hib = COLUMN_MAP[col]
        pr_str = f"{r['pr']}" if r['pr'] is not None else 'None'
        sig_str = f"{r['sigma']}" if r['sigma'] is not None else 'None'
        lines.append(
            f"    ({name!r:<28}, {tier!r:<8}, {str(hib):<5}, "
            f"{r['bl']}, {r['tr']}, {pr_str}, {sig_str}),"
        )
    lines.append("]")
    return "\n".join(lines)


def format_band_cmp(feat_rows, unaff_rows, rc_label):
    """Format BAND_CMP[rc_label] sub-dict."""
    feat_out = []
    unaff_out = []
    for col_name, display_name in BAND_CMP_KPIS_MAP.items():
        f = next((r for r in feat_rows if r['col'] == col_name), None)
        u = next((r for r in unaff_rows if r['col'] == col_name), None)
        if f and u:
            feat_out.append(f"({f['bl']},{f['tr']},{f['sigma'] or 0})")
            unaff_out.append(f"({u['bl']},{u['tr']},{u['sigma'] or 0})")

    lines = [
        f"    '{rc_label}': {{",
        f"        'feat':  [{', '.join(feat_out)}],",
        f"        'unaff': [{', '.join(unaff_out)}],",
        "    },",
    ]
    return "\n".join(lines)


def format_per_carrier(df, baseline_mask, trial_mask, rc_label, feature_bands):
    """Format PC_RCx dict."""
    lines = [f"PC_{rc_label} = {{"]
    for nokia_col, short_name in PER_CARRIER_MAP.items():
        if nokia_col not in df.columns:
            continue
        carrier_entries = []
        for band in sorted(feature_bands):
            band_mask_bl = baseline_mask & (df['BAND'] == band)
            band_mask_tr = trial_mask & (df['BAND'] == band)
            if band_mask_bl.sum() == 0:
                continue
            get_d = lambda mask: (
                df[mask].groupby('DATETIME')[nokia_col]
                .agg('mean' if is_mean(nokia_col) else 'sum').mean()
            )
            bl = round(get_d(band_mask_bl), 2)
            tr = round(get_d(band_mask_tr), 2)
            if not pd.isna(bl) and not pd.isna(tr):
                carrier_entries.append(f"'{band}':({bl},{tr})")
        if carrier_entries:
            lines.append(f"    {short_name!r:<14}: {{{', '.join(carrier_entries)}}},")
    lines.append("}")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Extract RAN trial statistics from Nokia export')
    parser.add_argument('--rc1-file',         required=True,  help='Path to RC1 Nokia KPI export Excel')
    parser.add_argument('--rc2-file',         default=None,   help='Path to RC2 Nokia KPI export Excel (optional)')
    parser.add_argument('--rc1-label',        default='RC3',  help='RC1 label (default: RC3)')
    parser.add_argument('--rc2-label',        default='RC4',  help='RC2 label (default: RC4)')
    parser.add_argument('--baseline-start',   required=True,  help='YYYY-MM-DD')
    parser.add_argument('--baseline-end',     required=True,  help='YYYY-MM-DD')
    parser.add_argument('--trial-start',      required=True,  help='YYYY-MM-DD')
    parser.add_argument('--trial-end',        required=True,  help='YYYY-MM-DD')
    parser.add_argument('--post-rb-start',    default=None,   help='YYYY-MM-DD (optional)')
    parser.add_argument('--post-rb-end',      default=None,   help='YYYY-MM-DD (optional)')
    parser.add_argument('--feature-bands',    required=True,  help='Comma-separated, e.g. B800,B900,B1800,B2100')
    parser.add_argument('--unaffected-bands', required=True,  help='Comma-separated, e.g. B700,B2300_F1,B2300_F2')
    parser.add_argument('--trial-id',         default='TRIAL', help='Used in output file names')
    parser.add_argument('--out-dir',          default='.',    help='Directory for CSV summary output')
    args = parser.parse_args()

    feature_bands   = set(args.feature_bands.split(','))
    unaffected_bands = set(args.unaffected_bands.split(','))

    bl_start = pd.Timestamp(args.baseline_start)
    bl_end   = pd.Timestamp(args.baseline_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    tr_start = pd.Timestamp(args.trial_start)
    tr_end   = pd.Timestamp(args.trial_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
    pr_start = pd.Timestamp(args.post_rb_start) if args.post_rb_start else None
    pr_end   = (pd.Timestamp(args.post_rb_end) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
                if args.post_rb_end else None)

    results = {}
    for rc_label, rc_file in [(args.rc1_label, args.rc1_file),
                               (args.rc2_label, args.rc2_file)]:
        if rc_file is None:
            continue
        print(f"\n=== Processing {rc_label}: {rc_file} ===", file=sys.stderr)
        df = load_and_filter(rc_file, DEFAULT_EARFCN_MAP)
        df = assign_band_groups(df, feature_bands, unaffected_bands)

        kpi_cols = [c for c in df.columns
                    if c in COLUMN_MAP or c in BAND_CMP_KPIS_MAP or c in PER_CARRIER_MAP]
        kpi_cols = list(dict.fromkeys(kpi_cols))  # deduplicate preserving order

        bl_mask = (df['DATETIME'] >= bl_start) & (df['DATETIME'] <= bl_end)
        tr_mask = (df['DATETIME'] >= tr_start) & (df['DATETIME'] <= tr_end)
        pr_mask = ((df['DATETIME'] >= pr_start) & (df['DATETIME'] <= pr_end)
                   if pr_start else None)

        feat_df  = df[df['BAND_GROUP'] == 'feat']
        unaff_df = df[df['BAND_GROUP'] == 'unaff']

        feat_bl_mask  = feat_df['DATETIME'].isin(df[bl_mask]['DATETIME'])
        feat_tr_mask  = feat_df['DATETIME'].isin(df[tr_mask]['DATETIME'])
        feat_pr_mask  = (feat_df['DATETIME'].isin(df[pr_mask]['DATETIME'])
                         if pr_mask is not None else None)
        unaff_bl_mask = unaff_df['DATETIME'].isin(df[bl_mask]['DATETIME'])
        unaff_tr_mask = unaff_df['DATETIME'].isin(df[tr_mask]['DATETIME'])

        # Re-derive masks directly on filtered dfs
        def pmask(sub_df, start, end):
            return (sub_df['DATETIME'] >= start) & (sub_df['DATETIME'] <= end)

        feat_stats  = compute_stats(feat_df, kpi_cols,
                                    pmask(feat_df, bl_start, bl_end),
                                    pmask(feat_df, tr_start, tr_end),
                                    pmask(feat_df, pr_start, pr_end) if pr_start else None)
        unaff_stats = compute_stats(unaff_df, kpi_cols,
                                    pmask(unaff_df, bl_start, bl_end),
                                    pmask(unaff_df, tr_start, tr_end),
                                    pmask(unaff_df, pr_start, pr_end) if pr_start else None)

        results[rc_label] = {
            'feat': feat_stats, 'unaff': unaff_stats, 'df': df,
            'bl_mask': pmask(df, bl_start, bl_end),
            'tr_mask': pmask(df, tr_start, tr_end),
        }

    # ── Output Python code ────────────────────────────────────────────────────
    sep = "\n" + "─" * 72 + "\n"
    print(sep)
    print("# ===== PASTE INTO build_stats_report_template.py =====\n")

    for rc_label in [args.rc1_label, args.rc2_label]:
        if rc_label not in results:
            continue
        feat_rows = results[rc_label]['feat']
        print(f"# {rc_label} — Feature Bands")
        print(format_feat_array(feat_rows, f'{rc_label}_FEAT'))
        print()

    print("BAND_CMP_KPIS = [")
    for v in BAND_CMP_KPIS_MAP.values():
        print(f"    {v!r},")
    print("]\n")
    print("BAND_CMP = {")
    for rc_label in [args.rc1_label, args.rc2_label]:
        if rc_label not in results:
            continue
        print(format_band_cmp(results[rc_label]['feat'],
                               results[rc_label]['unaff'], rc_label))
    print("}\n")

    for rc_label in [args.rc1_label, args.rc2_label]:
        if rc_label not in results:
            continue
        print(format_per_carrier(
            results[rc_label]['df'],
            results[rc_label]['bl_mask'],
            results[rc_label]['tr_mask'],
            rc_label, feature_bands))
        print()

    # ── Save CSV summary ──────────────────────────────────────────────────────
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    rows_csv = []
    for rc_label in [args.rc1_label, args.rc2_label]:
        if rc_label not in results:
            continue
        for grp_label, grp_rows in [('feat', results[rc_label]['feat']),
                                     ('unaff', results[rc_label]['unaff'])]:
            for r in grp_rows:
                col = r['col']
                dname, tier, hib = COLUMN_MAP.get(col, (col, '?', '?'))
                rows_csv.append({
                    'RC': rc_label, 'Group': grp_label, 'KPI': dname,
                    'Tier': tier, 'HigherBad': hib,
                    'BL': r['bl'], 'Trial': r['tr'], 'PostRB': r.get('pr'),
                    'Sigma': r['sigma'], 'BL_StdDev': r.get('bl_std'),
                    'SigmaNote': '*** near-zero variance ***' if r['sigma'] is None else '',
                })
    csv_path = out_dir / f"{args.trial_id}_stats_summary.csv"
    pd.DataFrame(rows_csv).to_csv(csv_path, index=False)
    print(f"\n# Summary CSV saved: {csv_path}", file=sys.stderr)
    print(f"# Review it to verify the computed values before running build_stats_report_template.py", file=sys.stderr)


if __name__ == '__main__':
    main()
