"""
build_kpi_charts_nr.py — NR KPI trend charts, per-RC (5G NSA)
==============================================================
Generates one KPI_Grouped Excel per RC.

SETUP CHECKLIST (edit the CONFIGURATION section below):
  1. Set TRIAL_ID, dates, and TRIAL_ROLLBACK (None if no rollback)
  2. Update MNO_NR_NRARFCN_MAP with your cluster's NRARFCNs
  3. Update MAIN_FILE, ES_FILE, OUT_DIR to your file paths
  4. Update the RCS list if your trial uses different RC labels

v1.1 — combine() bug fixed: both Trial and Rollback marker series are added
to a single combined chart object (one lc.combine() call).
"""
import warnings; warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import xlsxwriter
import xlsxwriter.utility as xu

# =============================================================================
# CONFIGURATION — edit all values in this section
# =============================================================================

TRIAL_ID       = 'CBXXXXXX'                          # ← EDIT: your trial ID
TRIAL_START    = pd.Timestamp('YYYY-MM-DD')           # ← EDIT: feature activation date
TRIAL_ROLLBACK = pd.Timestamp('YYYY-MM-DD')           # ← EDIT: rollback date, or None if no rollback
# TRIAL_ROLLBACK = None                               # ← uncomment if no rollback

# Period boundaries
BASELINE_START = pd.Timestamp('YYYY-MM-DD')           # ← EDIT
BASELINE_END   = pd.Timestamp('YYYY-MM-DD')           # ← EDIT
TRIAL_END      = pd.Timestamp('YYYY-MM-DD')           # ← EDIT (day before rollback, or trial end)
POST_RB_START  = pd.Timestamp('YYYY-MM-DD')           # ← EDIT (same as TRIAL_ROLLBACK if rollback)
POST_RB_END    = pd.Timestamp('YYYY-MM-DD')           # ← EDIT (last day of data)

# RCs to process — match the SUBNETWORK column values in your Nokia export
RCS = ['RC1']                                         # ← EDIT: e.g. ['RC3', 'RC4'] for two-RC trials

# NR carrier map — replace with your cluster's actual NRARFCNs
MNO_NR_NRARFCN_MAP = {
    152600: 'N28',      # ← EDIT: NRARFCN → carrier label
    635334: 'N78_F1',
    650666: 'N78_F2',
    652000: 'N78_F3',
}
CARRIER_ORDER = ['N28', 'N78_F1', 'N78_F2', 'N78_F3']  # ← EDIT: match your carriers
CARRIER_COLORS = {
    'N28':    '#D62728',
    'N78_F1': '#1F77B4',
    'N78_F2': '#2CA02C',
    'N78_F3': '#9467BD',
}

# Source files — update to your actual paths
MAIN_FILE = './5G_System_Program_Nokia_cluster_per_carrier.xlsx'  # ← EDIT
ES_FILE   = './5G_ES_Nokia_per_RC.xlsx'                           # ← EDIT
OUT_DIR   = './'                                                   # ← EDIT

# =============================================================================
# AGGREGATION RULES (generally no need to edit)
# =============================================================================
MEAN_KW = ['ratio','rate','efficiency','average','cqi','sinr','rssi','bler',
           'mcs','percentage','maximum','latency','delay','distribution',
           'usage','level','avg','pathloss','rank','starvation','headroom']
def is_mean(col): return any(k in col.lower() for k in MEAN_KW)

CHART_W = 780
CHART_H = 380

# =============================================================================
# KPI GROUP DEFINITIONS — edit chart titles/KPI column names to match your export
# =============================================================================
META_GROUPS = [
    dict(id='A', name='EnergySaving', title='Energy Saving',
         charts=[
             dict(sub='DRX Sleep Ratio',
                  y_title='DRX Sleep Ratio (%)',
                  kpis=[('DRX sleep time ratio', 'DRX_Sleep', '(%)')]),
             dict(sub='Reduced TX Power Saving Mode Ratio',
                  y_title='Reduced TX Power Saving Mode Ratio (%)',
                  kpis=[('Cell in Reduced TX Power Saving Mode Ratio', 'ReducedTX', '(%)')]),
             dict(sub='PDSCH Slot Usage Ratio',
                  y_title='PDSCH Slot Usage Ratio (%)',
                  kpis=[('Usage ratio of PDSCH data slots over all DL data slots', 'PDSCH_Slot', '(%)')]),
         ]),
    dict(id='B', name='Latency', title='Latency',
         charts=[
             dict(sub='Average DL Delay in CU-UP per Cell',
                  y_title='Avg DL Delay CU-UP (ms)',
                  kpis=[('Average delay DL in CU_UP per cell', 'DL_Delay', '(ms)')]),
             dict(sub='Average UL PDCP Re-ordering Delay',
                  y_title='UL PDCP Reorder Delay (ms)',
                  kpis=[('Average PDCP re_ordering delay in the UL per cell', 'UL_Reorder', '(ms)')]),
         ]),
    dict(id='C', name='Throughput', title='Throughput',
         charts=[
             dict(sub='Average MAC Layer User Throughput DL',
                  y_title='Avg MAC Tput DL (Mbps)',
                  kpis=[('Average MAC layer user throughput in downlink', 'MAC_Tput_DL', '(Mbps)')]),
             dict(sub='Maximum DL PDCP SDU NR Leg Throughput per DRB',
                  y_title='Max DL PDCP (kbps)',
                  kpis=[('Maximum DL PDCP SDU NR leg throughput per DRB', 'Max_PDCP_DL', '(kbps)')]),
             dict(sub='Maximum MAC Cell Throughput DL',
                  y_title='Max Cell Tput DL (kbps)',
                  kpis=[('Maximum MAC SDU Cell Throughput in DL on DTCH', 'Max_Cell_DL', '(kbps)')]),
             dict(sub='Maximum MAC Cell Throughput UL',
                  y_title='Max Cell Tput UL (kbps)',
                  kpis=[('Maximum MAC SDU Cell Throughput in UL on DTCH', 'Max_Cell_UL', '(kbps)')]),
         ]),
    dict(id='D', name='Accessibility', title='Accessibility',
         charts=[
             dict(sub='Accessibility Success Ratio',
                  y_title='Accessibility SR (%)',
                  kpis=[('Accessibility success ratio', 'Access_SR', '(%)')]),
             dict(sub='RRC Connection Establishment Success Ratio',
                  y_title='RRC SR (%)',
                  kpis=[('RRC connection establishment success ratio', 'RRC_SR', '(%)')]),
             dict(sub='Initial E-RAB Setup Success Ratio',
                  y_title='Init E-RAB SR (%)',
                  kpis=[('Initial E_RAB Setup Success Ratio', 'ERAB_SR', '(%)')]),
             dict(sub='NSA Call Accessibility (5G Side)',
                  y_title='NSA Accessibility (%)',
                  kpis=[('Non_Stand Alone call accessibility 5G side', 'NSA_Access', '(%)')]),
             dict(sub='Radio Admission Success Ratio for NSA User',
                  y_title='Radio Adm NSA SR (%)',
                  kpis=[('Radio admission success ratio for NSA user', 'Radio_Adm', '(%)')]),
             dict(sub='Active RACH Setup Success Ratio',
                  y_title='RACH SR (%)',
                  kpis=[('Active RACH setup success ratio', 'RACH_SR', '(%)')]),
         ]),
    dict(id='E', name='Retainability', title='Retainability',
         charts=[
             dict(sub='QoS Flow Drop Ratio — RAN View',
                  y_title='QoS Drop Ratio RAN (%)',
                  kpis=[('QoS Flow Drop Ratio _ RAN view', 'QoS_Drop_RAN', '(%)')]),
             dict(sub='QoS Flow Drop Ratio — User View (UE Lost)',
                  y_title='QoS Drop Ratio UEL (%)',
                  kpis=[('QoS Flow Drop Ratio _ User view_double_Ng mapped to UE lost', 'QoS_Drop_UEL', '(%)')]),
             dict(sub='Active E-RAB Drop Ratio — SgNB View',
                  y_title='E-RAB Drop Ratio (%)',
                  kpis=[('Active E_RAB Drop Ratio _ SgNB view', 'ERAB_Drop', '(%)')]),
             dict(sub='SgNB Triggered Abnormal Release Ratio',
                  y_title='SgNB Abn Rel Ratio (%)',
                  kpis=[('SgNB triggered abnormal release ratio excluding X2 reset', 'SgNB_Abn', '(%)')]),
         ]),
    dict(id='F', name='EN_DC', title='EN-DC / SgNB',
         charts=[
             dict(sub='SgNB Addition Preparation Success Ratio',
                  y_title='SgNB Add Prep SR (%)',
                  kpis=[('SgNB addition preparation success ratio', 'SgNB_Add', '(%)')]),
             dict(sub='SgNB Reconfiguration Success Ratio',
                  y_title='SgNB Reconfig SR (%)',
                  kpis=[('SgNB reconfiguration success ratio', 'SgNB_Reconf', '(%)')]),
             dict(sub='Number of SgNB Addition Requests',
                  y_title='SgNB Add Requests (count)',
                  kpis=[('Number of SgNB addition requests', 'SgNB_Req', '(count)')]),
             dict(sub='UE Redirections to E-UTRAN (Voice Fallback)',
                  y_title='EPS Fallback (count)',
                  kpis=[('Number of UE redirections to E_UTRAN due to voice fallback to LTE', 'EPS_FB', '(count)')]),
         ]),
    dict(id='G', name='PDCCH', title='PDCCH (Watchdog)',
         charts=[
             dict(sub='Average PDCCH CCE Starvation Ratio',
                  y_title='CCE Starvation Ratio (%)',
                  kpis=[('Average PDCCH CCE starvation ratio in cell', 'CCE_Starv', '(%)')]),
             dict(sub='Average PDCCH Aggregation Level — DL',
                  y_title='PDCCH AGG Level DL',
                  kpis=[('Average aggregation level used on PDCCH downlink grants', 'AGG_DL', '')]),
             dict(sub='Average PDCCH Aggregation Level — UL',
                  y_title='PDCCH AGG Level UL',
                  kpis=[('Average aggregation level used on PDCCH uplink grants', 'AGG_UL', '')]),
         ]),
    dict(id='H', name='Mobility', title='Mobility',
         charts=[
             dict(sub='Intra-DU Intra-Frequency HO Success Ratio',
                  y_title='HO SR (%)',
                  kpis=[('Intra_frequency Intra_gNB Intra_DU handover total success ratio', 'IF_Intra_HO', '(%)')]),
             dict(sub='Intra-DU Inter-Frequency HO Success Ratio',
                  y_title='HO SR (%)',
                  kpis=[('Intra_gNB Intra_DU Inter_frequency HO total success ratio per PLMN', 'XF_Intra_HO', '(%)')]),
             dict(sub='Xn-Based Inter-gNB HO Success Ratio',
                  y_title='HO SR (%)',
                  kpis=[('Intra_frequency Xn based Inter_gNB handover execution success ratio per PLMN', 'Xn_HO', '(%)')]),
             dict(sub='Inter-gNB HO Success Ratio for NSA',
                  y_title='HO SR (%)',
                  kpis=[('Inter gNB handover success ratio for NSA', 'Inter_gNB_HO', '(%)')]),
             dict(sub='PSCell Change Success Ratio',
                  y_title='PSCell Change SR (%)',
                  kpis=[('Intra_frequency intra_DU PSCell change total success ratio', 'PSCell_SR', '(%)')]),
         ]),
    dict(id='I', name='RadioQuality', title='Radio Quality',
         charts=[
             dict(sub='Average Wideband CQI — 256QAM Table',
                  y_title='CQI 256QAM',
                  kpis=[('Average wideband CQI 256QAM table', 'CQI_256', '')]),
             dict(sub='Average Wideband CQI — 64QAM Table',
                  y_title='CQI 64QAM',
                  kpis=[('Average wideband CQI 64QAM table', 'CQI_64', '')]),
             dict(sub='Average UE SINR for PUSCH (Rank 1)',
                  y_title='SINR PUSCH Rank1 (dB)',
                  kpis=[('Average UE related SINR for PUSCH in Rank 1', 'SINR_PUSCH', '(dB)')]),
             dict(sub='Average UE SINR for PUCCH',
                  y_title='SINR PUCCH (dB)',
                  kpis=[('Average UE related SINR for PUCCH', 'SINR_PUCCH', '(dB)')]),
             dict(sub='Average UE Pathloss Level for PUSCH',
                  y_title='Pathloss PUSCH (dB)',
                  kpis=[('Average UE pathloss level for PUSCH', 'PL_PUSCH', '(dB)')]),
             dict(sub='Average Rank Used in Downlink',
                  y_title='DL Rank',
                  kpis=[('Average rank used in downlink', 'DL_Rank', '')]),
         ]),
    dict(id='J', name='Traffic', title='Traffic / Load',
         charts=[
             dict(sub='PRB Utilisation — DL (PDSCH)',
                  y_title='PRB Util DL (%)',
                  kpis=[('PRB utilization for PDSCH', 'PRB_DL', '(%)')]),
             dict(sub='PRB Utilisation — UL (PUSCH)',
                  y_title='PRB Util UL (%)',
                  kpis=[('PRB utilization for PUSCH', 'PRB_UL', '(%)')]),
             dict(sub='Average Number of NSA Users',
                  y_title='Avg NSA Users',
                  kpis=[('Average number of NSA users in selected area', 'NSA_Users', '')]),
             dict(sub='MAC DL Data Volume on DTCH',
                  y_title='DL Data Volume (MB)',
                  kpis=[('MAC SDU data volume transmitted in DL on DTCH', 'DL_Vol', '(MB)')]),
             dict(sub='Average Active DL UEs with Data in Buffer',
                  y_title='Active DL UEs',
                  kpis=[('Average number of active UEs with data in the buffer for DRBs in DL', 'Active_DL_UE', '')]),
         ]),
]

BTS_ENERGY_CHARTS = [
    dict(sub='Total BTS Energy Consumption',  y_title='Total BTS Energy (Wh)',      col='[N]ENERGY_CONSUMPTION_IN_BTS',  short='BTS_Energy'),
    dict(sub='RU Energy Consumption',         y_title='RU Energy Consumption (Wh)', col='[N]RU_ENERGY_CONSUMPTION',      short='RU_Energy'),
    dict(sub='RF Energy Consumption',         y_title='RF Energy Consumption (Wh)', col='[N]ENERGY_CONSUMPTION_IN_RF',   short='RF_Energy'),
    dict(sub='System Module (SM) Energy',     y_title='SM Energy Consumption (Wh)', col='[N]ENERGY_CONSUMPTION_IN_SM',   short='SM_Energy'),
    dict(sub='RU Average Power Usage',        y_title='RU Avg Power Usage (W)',     col='[N]RU_AVG_PWR_USAGE',           short='RU_Avg_Pwr'),
    dict(sub='RU Max Power Usage',            y_title='RU Max Power Usage (W)',     col='[N]RU_MAX_PWR_USAGE',           short='RU_Max_Pwr'),
    dict(sub='RU Min Power Usage',            y_title='RU Min Power Usage (W)',     col='[N]RU_MIN_PWR_USAGE',           short='RU_Min_Pwr'),
]
BTS_ENERGY_COLOR = '#8B4513'

# =============================================================================
# PHASE CLASSIFICATION
# =============================================================================
def phase(dt):
    if dt < TRIAL_START:
        return 'Baseline'
    if TRIAL_ROLLBACK is not None and dt >= TRIAL_ROLLBACK:
        return 'Post-RB'
    return 'Trial'

# =============================================================================
# DATA LOADERS
# =============================================================================
def load_main(rc_label):
    print(f'  Loading main KPI file for {rc_label} …')
    df = pd.read_excel(MAIN_FILE, engine='openpyxl')
    df.columns = df.columns.str.strip()
    dt_col = next((c for c in df.columns if c.upper() in ('DATETIME','DATE','PERIOD START TIME')), df.columns[0])
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce').dt.normalize()
    df = df.dropna(subset=['DATETIME'])
    if 'SUBNETWORK' in df.columns:
        df = df[df['SUBNETWORK'] == rc_label].copy()
    nr_col = next((c for c in df.columns if 'NRARFCN' in c.upper()), None)
    if nr_col:
        df['NRARFCN'] = pd.to_numeric(df[nr_col], errors='coerce')
        df = df[df['NRARFCN'].isin(MNO_NR_NRARFCN_MAP)].copy()
        df['CARRIER'] = df['NRARFCN'].map(MNO_NR_NRARFCN_MAP)
    excl = {'DATETIME','NRARFCN','CARRIER','SUBNETWORK'}
    if nr_col: excl.add(nr_col)
    kpis = [c for c in df.columns if c not in excl]
    agg  = {c: ('mean' if is_mean(c) else 'sum') for c in kpis}
    result = df.groupby(['DATETIME','CARRIER']).agg(agg).reset_index()
    print(f'    RC={rc_label}, Carriers: {sorted(result["CARRIER"].unique())}')
    print(f'    Dates: {result["DATETIME"].nunique()}  ({result["DATETIME"].min().date()} → {result["DATETIME"].max().date()})')
    return result


def load_es(rc_label):
    print(f'  Loading ES file for {rc_label} …')
    df = pd.read_excel(ES_FILE, engine='openpyxl')
    df.columns = df.columns.str.strip()
    dt_col = next((c for c in df.columns if c.upper() in ('DATETIME','DATE','PERIOD START TIME')), df.columns[0])
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce').dt.normalize()
    df = df.dropna(subset=['DATETIME'])
    if 'SUBNETWORK' in df.columns:
        df = df[df['SUBNETWORK'] == rc_label].copy()
    kpis = [c for c in df.columns if c not in ('DATETIME','SUBNETWORK')]
    agg  = {c: 'sum' for c in kpis}
    result = df.groupby('DATETIME').agg(agg).reset_index()
    print(f'    Dates: {result["DATETIME"].nunique()}')
    return result


# =============================================================================
# WORKBOOK BUILDER
# =============================================================================
def build(rc_label, main_df, es_df, carriers, out_path):
    wb = xlsxwriter.Workbook(out_path, {'nan_inf_to_errors': True})

    # ── Formats ──────────────────────────────────────────────────────────────
    fmt_hdr   = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 9,
                                'font_color': '#FFFFFF', 'bg_color': '#1F3864',
                                'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 0})
    fmt_date  = wb.add_format({'num_format': 'DD-MMM-YYYY', 'font_name': 'Arial', 'font_size': 9})
    fmt_num   = wb.add_format({'font_name': 'Arial', 'font_size': 9, 'num_format': '#,##0.00'})
    fmt_str   = wb.add_format({'font_name': 'Arial', 'font_size': 9})
    fmt_title = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 18,
                                'font_color': '#FFFFFF', 'bg_color': '#1F3864',
                                'align': 'center', 'valign': 'vcenter'})
    fmt_lbl   = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10})
    fmt_val   = wb.add_format({'font_name': 'Arial', 'font_size': 10})
    fmt_sub   = wb.add_format({'italic': True, 'font_name': 'Arial', 'font_size': 8, 'font_color': '#555555'})
    fmt_ctitle= wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 14, 'font_color': '#1F3864'})
    fmt_clbl  = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10, 'font_color': '#2F5496'})
    carrier_fmts = {c: wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10,
                                       'font_color': CARRIER_COLORS.get(c, '#888888')}) for c in CARRIER_ORDER}

    _fmt_cache = {}
    def row_fmts(ph):
        if ph not in _fmt_cache:
            bg = '#FFFDE7' if ph == 'Trial' else ('#E8F5E9' if ph == 'Post-RB' else None)
            if bg:
                _fmt_cache[ph] = (
                    wb.add_format({'num_format': 'DD-MMM-YYYY', 'font_name': 'Arial', 'font_size': 9, 'bg_color': bg}),
                    wb.add_format({'font_name': 'Arial', 'font_size': 9, 'num_format': '#,##0.00', 'bg_color': bg}),
                    wb.add_format({'font_name': 'Arial', 'font_size': 9, 'bg_color': bg}),
                )
            else:
                _fmt_cache[ph] = (fmt_date, fmt_num, fmt_str)
        return _fmt_cache[ph]

    dates = sorted(main_df['DATETIME'].unique())
    n     = len(dates)

    # ── Cover ────────────────────────────────────────────────────────────────
    print(f'  Building Cover …')
    wc = wb.add_worksheet('Cover')
    wc.hide_gridlines(2)
    wc.set_column('A:A', 46); wc.set_column('B:B', 60)
    wc.set_row(0, 52)
    wc.merge_range('A1:B1', f'5G NR KPI Performance Report — {rc_label}  ({TRIAL_ID})', fmt_title)

    rb_date_str = TRIAL_ROLLBACK.strftime('%d %B %Y') if TRIAL_ROLLBACK is not None else 'N/A'
    meta = [
        ('Trial ID:',              TRIAL_ID),
        ('Technology:',            'NR NSA (EN-DC)'),
        ('Trial start:',           TRIAL_START.strftime('%d %B %Y')),
        ('Rollback date:',         rb_date_str),
        ('Baseline period:',       f'{BASELINE_START.date()} → {BASELINE_END.date()}'),
        ('Trial period:',          f'{TRIAL_START.date()} → {TRIAL_END.date()}'),
        ('Post-RB period:',        f'{POST_RB_START.date()} → {POST_RB_END.date()}' if TRIAL_ROLLBACK is not None else 'N/A'),
        ('RC:',                    rc_label),
        ('Carriers in scope:',     ', '.join(carriers)),
        ('Stratification:',        'Carrier-only (NR NSA methodology — no Feature/Unaffected split)'),
        ('Aggregation:',           'Counters → SUM; Ratios → MEAN per carrier'),
        ('', ''),
        ('Row shading (D-tabs):',  ''),
        ('', 'Yellow = Trial active'),
        ('', 'Light green = Post-RB'),
        ('', ''),
        ('Chart markers:',         ''),
        ('', 'Red bar = Trial implementation date'),
        ('', 'Green bar = Rollback date (if applicable)'),
        ('', '(Secondary Y axis 0–1 on right side)'),
        ('', ''),
        ('D-tabs (raw data):',     'Hidden — right-click sheet tab → Unhide to access'),
    ]
    for i, row_data in enumerate(meta, start=1):
        wc.set_row(i, 16)
        lbl, val = row_data[0], row_data[1]
        wc.write(i, 0, lbl, fmt_lbl if lbl else fmt_val)
        wc.write(i, 1, val, fmt_val)

    # ── Agg_Data ─────────────────────────────────────────────────────────────
    print(f'  Building Agg_Data …')
    wp = wb.add_worksheet('Agg_Data')
    wp.freeze_panes(1, 2)
    agg_cols = [c for c in main_df.columns if c not in ('DATETIME','CARRIER')]
    hdr_agg  = ['Date','Carrier'] + agg_cols
    wp.set_row(0, 42)
    for ci, h in enumerate(hdr_agg):
        wp.write(0, ci, h, fmt_hdr)
    wp.set_column(0,0,13); wp.set_column(1,1,12)
    for ri, (_, row) in enumerate(main_df.sort_values(['DATETIME','CARRIER']).iterrows(), start=1):
        ph = phase(row['DATETIME'])
        fd, fn, fs = row_fmts(ph)
        wp.write_datetime(ri, 0, row['DATETIME'].to_pydatetime(), fd)
        wp.write(ri, 1, row['CARRIER'], fs)
        for ci, c in enumerate(agg_cols, start=2):
            v = row[c]
            if isinstance(v, float) and np.isnan(v):
                wp.write_blank(ri, ci, None, fn)
            else:
                wp.write_number(ri, ci, float(v) if isinstance(v, (np.floating, float)) else int(v), fn)

    # ── KPI groups ────────────────────────────────────────────────────────────
    for mg in META_GROUPS:
        all_kpis   = [(col,sh,un,ci,ki) for ci,chart in enumerate(mg['charts'])
                      for ki,(col,sh,un) in enumerate(chart['kpis'])]
        avail_kpis = [(col,sh,un,ci,ki) for (col,sh,un,ci,ki) in all_kpis
                      if col in main_df.columns and not main_df[col].isna().all()]
        if not avail_kpis:
            print(f'  Skipping {mg["name"]} — no columns found')
            continue
        print(f'  Building {mg["name"]} ({len(avail_kpis)} KPI series) …')

        d_name = f'D_{mg["name"]}'[:31]
        c_name = f'C_{mg["name"]}'[:31]

        # D-tab (raw data)
        ds = wb.add_worksheet(d_name)
        ds.freeze_panes(1, 1)
        ds.set_column(0,0,13); ds.set_row(0,42)

        hdr_d = ['Date']; col_map = {}; cursor = 1
        for col,sh,un,ci,ki in avail_kpis:
            if ci not in col_map: col_map[ci] = {}
            if ki not in col_map[ci]: col_map[ci][ki] = {}
            for carrier in carriers:
                hdr_d.append(f'{sh}_{carrier}')
                col_map[ci][ki][carrier] = cursor
                ds.set_column(cursor,cursor,12); cursor += 1
        trial_col  = cursor; hdr_d.append('Trial_Start'); cursor += 1
        rb_col     = cursor; hdr_d.append('Rollback');    cursor += 1
        phase_col  = cursor; hdr_d.append('Phase');       cursor += 1
        ncols = cursor

        for ci2,h in enumerate(hdr_d):
            ds.write(0,ci2,h,fmt_hdr)

        for ri, dt in enumerate(dates, start=1):
            ph = phase(dt)
            fd, fn, fs = row_fmts(ph)
            ds.write_datetime(ri, 0, dt.to_pydatetime(), fd)
            for col,sh,un,ci,ki in avail_kpis:
                for carrier in carriers:
                    mask = (main_df['DATETIME']==dt)&(main_df['CARRIER']==carrier)
                    sub  = main_df.loc[mask, col]
                    val  = float(sub.iloc[0]) if (len(sub)>0 and not sub.isna().all()) else None
                    c_i  = col_map[ci][ki][carrier]
                    if val is None or (isinstance(val,float) and np.isnan(val)):
                        ds.write_blank(ri, c_i, None, fn)
                    else:
                        ds.write_number(ri, c_i, val, fn)
            ds.write_number(ri, trial_col, 1.0 if dt==TRIAL_START else 0.0, fn)
            ds.write_number(ri, rb_col,    1.0 if (TRIAL_ROLLBACK is not None and dt==TRIAL_ROLLBACK) else 0.0, fn)
            ds.write(ri, phase_col, ph, fs)

        last_ltr = xu.xl_col_to_name(ncols-1)
        ph_ltr   = xu.xl_col_to_name(phase_col)
        ds.conditional_format(f'A2:{last_ltr}{n+1}', {
            'type': 'formula', 'criteria': f'=${ph_ltr}2="Trial"',
            'format': wb.add_format({'bg_color': '#FFFDE7'})})
        ds.conditional_format(f'A2:{last_ltr}{n+1}', {
            'type': 'formula', 'criteria': f'=${ph_ltr}2="Post-RB"',
            'format': wb.add_format({'bg_color': '#E8F5E9'})})
        ds.hide()

        # C-tab (charts)
        cs = wb.add_worksheet(c_name)
        cs.hide_gridlines(2)
        cs.set_column('A:A',4)
        cs.set_row(0,26); cs.set_row(1,14)
        cs.write(0,0, f'{rc_label}  │  {mg["title"]}', fmt_ctitle)
        rb_hint = f'  │  Green bar = Rollback' if TRIAL_ROLLBACK is not None else ''
        cs.write(1,0, (f'Trial {TRIAL_START.strftime("%d-%b-%Y")}{rb_hint}  │  '
                       f'Red bar = Trial start  │  Yellow = Trial  │  Green = Post-RB'), fmt_sub)

        row_anchor = 2
        charts_avail = {}
        for col,sh,un,ci,ki in avail_kpis:
            if ci not in charts_avail: charts_avail[ci] = []
            charts_avail[ci].append((col,sh,un,ki))

        for ci in sorted(charts_avail.keys()):
            chart_def   = mg['charts'][ci]
            kpi_entries = charts_avail[ci]
            cs.set_row(row_anchor,16)
            cs.write(row_anchor,0, f'  {chart_def["sub"]}', fmt_clbl)
            row_anchor += 1

            lc = wb.add_chart({'type': 'line'})
            lc.set_size({'width': CHART_W, 'height': CHART_H})
            lc.set_legend({'position': 'right'})
            lc.set_x_axis({'date_axis': True, 'num_format': 'dd-mmm', 'major_unit': 7, 'major_unit_type': 'days'})
            lc.set_y_axis({'name': chart_def['y_title'], 'num_format': '#,##0.00'})
            lc.set_y2_axis({'min':0,'max':1,'num_format':';;;','major_gridlines':{'visible':False}})

            for col,sh,un,ki in kpi_entries:
                for carrier in carriers:
                    c_i = col_map[ci][ki][carrier]
                    lc.add_series({'name': [d_name,0,c_i], 'categories': [d_name,1,0,n,0],
                                   'values': [d_name,1,c_i,n,c_i],
                                   'line': {'color': CARRIER_COLORS.get(carrier,'#888888'), 'width':1.5},
                                   'marker': {'type':'none'}})

            # ── Marker bars — FIX: both series in ONE combined chart (single combine() call) ──
            # xlsxwriter only honours one combine() per chart. Both series must be
            # added to a single secondary chart before the combine() call.
            bc_markers = wb.add_chart({'type': 'column'})
            bc_markers.add_series({'name': [d_name,0,trial_col], 'categories': [d_name,1,0,n,0],
                                    'values': [d_name,1,trial_col,n,trial_col],
                                    'fill': {'color':'#CC0000','transparency':20},
                                    'border': {'none':True}, 'y2_axis': True})
            if TRIAL_ROLLBACK is not None:
                bc_markers.add_series({'name': [d_name,0,rb_col], 'categories': [d_name,1,0,n,0],
                                        'values': [d_name,1,rb_col,n,rb_col],
                                        'fill': {'color':'#00AA00','transparency':20},
                                        'border': {'none':True}, 'y2_axis': True})
            lc.combine(bc_markers)   # ← single combine() call

            cs.insert_chart(row_anchor, 0, lc, {'x_offset':5,'y_offset':5})
            row_anchor += 22

    # ── BTS Energy (per-RC ES data) ───────────────────────────────────────────
    print(f'  Building BTS_Energy …')
    es_dates = sorted(es_df['DATETIME'].unique())
    ne = len(es_dates)
    avail_bts = [c for c in BTS_ENERGY_CHARTS if c['col'] in es_df.columns]

    if avail_bts:
        dbe = wb.add_worksheet('D_BTS_Energy')
        dbe.freeze_panes(1,1); dbe.set_column(0,0,13); dbe.set_row(0,42)
        hdr_bts  = ['Date'] + [c['short'] for c in avail_bts] + ['Trial_Start','Rollback','Phase']
        bts_cmap = {c['short']: i+1 for i,c in enumerate(avail_bts)}
        bts_trial_col = len(avail_bts)+1
        bts_rb_col    = len(avail_bts)+2
        bts_phase_col = len(avail_bts)+3
        for ci2,h in enumerate(hdr_bts):
            dbe.write(0,ci2,h,fmt_hdr)
        for ci2 in range(1,len(hdr_bts)):
            dbe.set_column(ci2,ci2,18)

        for ri,dt in enumerate(es_dates, start=1):
            ph = phase(dt)
            fd, fn, fs = row_fmts(ph)
            dbe.write_datetime(ri,0, dt.to_pydatetime(), fd)
            mask = es_df['DATETIME']==dt
            for ch in avail_bts:
                sub = es_df.loc[mask, ch['col']]
                val = float(sub.iloc[0]) if len(sub)>0 and not sub.isna().all() else None
                c_i = bts_cmap[ch['short']]
                if val is None or (isinstance(val,float) and np.isnan(val)):
                    dbe.write_blank(ri, c_i, None, fn)
                else:
                    dbe.write_number(ri, c_i, val, fn)
            dbe.write_number(ri, bts_trial_col, 1.0 if dt==TRIAL_START else 0.0, fn)
            dbe.write_number(ri, bts_rb_col,    1.0 if (TRIAL_ROLLBACK is not None and dt==TRIAL_ROLLBACK) else 0.0, fn)
            dbe.write(ri, bts_phase_col, ph, fs)

        last_ltr = xu.xl_col_to_name(bts_phase_col)
        ph_ltr   = xu.xl_col_to_name(bts_phase_col)
        dbe.conditional_format(f'A2:{last_ltr}{ne+1}', {
            'type':'formula','criteria': f'=${ph_ltr}2="Trial"',
            'format': wb.add_format({'bg_color':'#FFFDE7'})})
        dbe.conditional_format(f'A2:{last_ltr}{ne+1}', {
            'type':'formula','criteria': f'=${ph_ltr}2="Post-RB"',
            'format': wb.add_format({'bg_color':'#E8F5E9'})})
        dbe.hide()

        cbe = wb.add_worksheet('C_BTS_Energy')
        cbe.hide_gridlines(2); cbe.set_column('A:A',4)
        cbe.set_row(0,26); cbe.set_row(1,14)
        cbe.write(0,0, f'{rc_label}  │  BTS / RU Energy (per RC — ES cluster file)', fmt_ctitle)
        cbe.write(1,0, f'ES report filtered to {rc_label}  │  Red bar = Trial start  │  Green bar = Rollback', fmt_sub)

        row_anchor = 2
        for ch in avail_bts:
            c_i = bts_cmap[ch['short']]
            cbe.set_row(row_anchor,16)
            cbe.write(row_anchor,0, f'  {ch["sub"]}', fmt_clbl)
            row_anchor += 1

            lc = wb.add_chart({'type': 'line'})
            lc.set_size({'width': CHART_W, 'height': CHART_H})
            lc.set_legend({'position': 'right'})
            lc.set_x_axis({'date_axis': True, 'num_format': 'dd-mmm', 'major_unit':7, 'major_unit_type':'days'})
            lc.set_y_axis({'name': ch['y_title'], 'num_format': '#,##0'})
            lc.set_y2_axis({'min':0,'max':1,'num_format':';;;','major_gridlines':{'visible':False}})
            lc.add_series({'name': ['D_BTS_Energy',0,c_i], 'categories': ['D_BTS_Energy',1,0,ne,0],
                           'values': ['D_BTS_Energy',1,c_i,ne,c_i],
                           'line': {'color': BTS_ENERGY_COLOR, 'width':2.0}, 'marker':{'type':'none'}})
            bc_markers_bts = wb.add_chart({'type':'column'})
            bc_markers_bts.add_series({'name':['D_BTS_Energy',0,bts_trial_col],
                             'categories':['D_BTS_Energy',1,0,ne,0],
                             'values':['D_BTS_Energy',1,bts_trial_col,ne,bts_trial_col],
                             'fill':{'color':'#CC0000','transparency':20},'border':{'none':True},'y2_axis':True})
            if TRIAL_ROLLBACK is not None:
                bc_markers_bts.add_series({'name':['D_BTS_Energy',0,bts_rb_col],
                                 'categories':['D_BTS_Energy',1,0,ne,0],
                                 'values':['D_BTS_Energy',1,bts_rb_col,ne,bts_rb_col],
                                 'fill':{'color':'#00AA00','transparency':20},'border':{'none':True},'y2_axis':True})
            lc.combine(bc_markers_bts)
            cbe.insert_chart(row_anchor, 0, lc, {'x_offset':5,'y_offset':5})
            row_anchor += 22

    wb.close()
    print(f'\n[saved] {out_path}')


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == '__main__':
    for rc in RCS:
        print(f'\n{"="*60}\nNR KPI Charts — {TRIAL_ID} {rc}\n{"="*60}')
        main_df = load_main(rc)
        es_df   = load_es(rc)
        carriers = [c for c in CARRIER_ORDER if c in main_df['CARRIER'].values]
        print(f'  Active carriers: {carriers}')
        out_path = f'{OUT_DIR}{TRIAL_ID}_{rc}_NR_KPI_Grouped.xlsx'
        build(rc, main_df, es_df, carriers, out_path)
        print(f'✓ {rc} done.')
    print('\n✓ All RCs complete.')
