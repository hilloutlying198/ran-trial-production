# =============================================================================
# KPI CHARTS EXCEL GENERATOR — ran-trial-production skill template
# =============================================================================
# REFERENCE TRIAL: CBXXXXXX (MNO 4G, RC3/RC4, Nokia KPI engine export)
#
# INPUT: One or two Nokia KPI engine Excel exports (one per RC/SW version)
# OUTPUT: <TRIAL_ID>_KPI_Grouped.xlsx — 22 sheets, ~54 charts
#
# TO ADAPT FOR A NEW TRIAL:
#   1. Update TRIAL_START and TRIAL_ROLLBACK dates (~line 34)
#   2. Update MNO_EARFCN_MAP (~line 40) — map EARFCN integers to band labels
#      Get EARFCNs from the source file's EARFCN column header or carrier plan
#   3. Update SOURCE_FILES dict (~line 50 area) with paths to the new RC exports
#   4. Update OUT_PATH with new TRIAL_ID
#   5. If the operator is not MNO, rename the filter logic to match
#
# DO NOT CHANGE: KPI group definitions, chart layout logic, format helpers,
# aggregation rules. These match the approved template (Temaplate_KPI_Grouped.xlsx).
# =============================================================================
"""
Nokia 4G KPI Report — grouped sheets v2
========================================
Key changes vs v1 (build_grouped.py):
  1. MNO-only EARFCN filter: rows from non-MNO carriers (VF, unknown)
     are removed before any aggregation.
  2. B2300 is kept as TWO separate carriers (B2300_F1 / B2300_F2)
     instead of merging them. Merging caused ratio KPIs >100%.
  3. Chart layout matches user-approved template (Temaplate_KPI_Grouped.xlsx):
     - One KPI per chart (DL and UL split into separate charts)
     - RACH+CBRACH combined, SINR PUCCH+PUSCH combined, SE DL+UL combined
  4. UL BLER added to Quality group.
  5. Extended KPI coverage (v2.1):
     - Energy Saving: DRX Sleep Ratio added
     - Traffic: PDCP SDU Volume DL/UL and Active UEs UL added
     - Quality: Initial BLER (PDSCH), 256QAM CQI, RLC Retx DL/UL added
     - New Group I — MCS & Radio: avg MCS, MCS distribution, power headroom,
       UL power %, RTWP, AGG level / blocking, PDCCH symbols
     - New Group J — Latency: latency DL/UL, PDCP SDU delay per QCI
  6. D_xxx data sheets are hidden (visible via right-click → Unhide) to
     reduce navigation clutter; charts remain fully interactive.

Reference files:
  references/lte/carrier_allocation.md — MNO EARFCN → carrier label mapping
  Temaplate_KPI_Grouped.xlsx — approved chart layout
"""
import warnings; warnings.filterwarnings('ignore')
import pandas as pd
import numpy as np
import xlsxwriter
import xlsxwriter.utility as xu

# ─── Trial dates ─────────────────────────────────────────────
TRIAL_START    = pd.Timestamp('YYYY-MM-DD')   # ← EDIT
TRIAL_ROLLBACK = pd.Timestamp('YYYY-MM-DD')   # ← EDIT: or None

# ─── MNO carrier filter (from references/lte/carrier_allocation.md) ─────────
# Only rows whose EARFCN is in this map are kept.
# B2300 is split into F1 (39250) and F2 (39448) — they must NOT be merged.
MNO_EARFCN_MAP = {
    9260:  'B700',
    6400:  'B800',
    3725:  'B900',
    1226:  'B1800',
    347:   'B2100',
    39250: 'B2300_F1',
    39448: 'B2300_F2',
}

# Canonical display order
CARRIER_ORDER = ['B700', 'B800', 'B900', 'B1800', 'B2100', 'B2300_F1', 'B2300_F2']

# Colours per carrier (RRGGBB hex with #)
CARRIER_COLORS = {
    'B700':     '#D62728',   # red
    'B800':     '#F5A623',   # orange
    'B900':     '#B8B800',   # olive
    'B1800':    '#2CA02C',   # green
    'B2100':    '#1F77B4',   # blue
    'B2300_F1': '#9467BD',   # purple
    'B2300_F2': '#E377C2',   # pink
}

# ─── Aggregation rules ───────────────────────────────────────
# KPIs that contain any of these keywords are averaged (MEAN).
# All other KPIs are summed (SUM) — they are raw counters.
MEAN_KW = ['ratio','rate','efficiency','average','cqi','sinr','rssi','bler',
           'mcs','percentage','maximum','latency','delay','distribution',
           'usage','rbler','level','headroom','offset','spectral','avg ue',
           'avg level','agg level','symbol']

def is_mean(col): return any(k in col.lower() for k in MEAN_KW)

# ─── KPI group definitions ───────────────────────────────────
# Layout approved by user via Temaplate_KPI_Grouped.xlsx.
# Each meta-group → one D-tab (data) + one C-tab (charts).
# Each chart entry → one chart on the C-tab (one or two KPIs).
# 'sub'     : label text shown above chart on C-tab
# 'y_title' : Y-axis title (matches template)
# 'kpis'    : list of (source_column_name, short_label, unit_string)

META_GROUPS = [
    dict(id='A', name='EnergySaving', title='Energy Saving Mode Activity',
         charts=[
             dict(sub='Power Saving Mode Ratio',
                  y_title='Power Saving Mode Ratio  (%)',
                  kpis=[('Cell in Power Saving Mode Ratio', 'PSM_Ratio', '(%)')]),
             dict(sub='Reduced TX Power Saving Mode Ratio',
                  y_title='Reduced TX Power Saving Mode Ratio  (%)',
                  kpis=[('Cell in Reduced TX Power Saving Mode Ratio', 'ReducedTX', '(%)')]),
             dict(sub='DRX Sleep Ratio',
                  y_title='DRX Sleep Ratio  (%)',
                  kpis=[('DRX Sleep Ratio', 'DRX_Sleep', '(%)')]),
         ]),

    dict(id='B', name='Accessibility', title='Accessibility',
         charts=[
             dict(sub='Cell Availability',
                  y_title='Cell Availability  (%)',
                  kpis=[('Cell Availability Ratio', 'Availability', '(%)')]),
             dict(sub='RACH & CB-RACH Setup Success Rates',
                  y_title='RACH & RRC Connection Setup Success Rates  (%)',
                  kpis=[('RACH Setup Completion Success Rate',
                          'RACH_SR', '(%)'),
                        ('Complete Contention Based RACH Setup Success Rate',
                          'CBRACH_SR', '(%)')]),
             dict(sub='E-RAB Setup Success Ratio',
                  y_title='E-RAB Setup Success Rates  (%)',
                  kpis=[('E_RAB Setup Success Ratio', 'ERAB_SR', '(%)')]),
             dict(sub='RRC Connection Setup Success Ratio',
                  y_title='RACH & RRC Connection Setup Success Rates  (%)',
                  kpis=[('Total RRC Connection Setup Success Ratio', 'RRC_SR', '(%)')]),
             dict(sub='Initial E-RAB Accessibility',
                  y_title='E-RAB Setup Success Rates  (%)',
                  kpis=[('Initial E_RAB Accessibility', 'ERAB_Init', '(%)')]),
         ]),

    dict(id='C', name='Retainability', title='Retainability',
         charts=[
             dict(sub='E-RAB Retainability — GBR (RAN View)',
                  y_title='E-RAB Retainability (RAN View)  (%)',
                  kpis=[('E_RAB Retainability Rate RAN View RNL Failure with UE Lost',
                          'ERAB_Retain', '(%)')]),
             dict(sub='E-RAB Retainability — non-GBR (RAN View)',
                  y_title='E-RAB Retainability (RAN View)  (%)',
                  kpis=[('non GBR E_RAB Retainability Rate RAN View RNL Failure with UE Lost',
                          'nonGBR_Retain', '(%)')]),
             dict(sub='RRC Re-establishment Success Ratio',
                  y_title='RRC Re-establishment & E-RAB Drop  (%)',
                  kpis=[('Total RRC Connection Re_establishment Success Ratio',
                          'Reestab_SR', '(%)')]),
             dict(sub='E-RAB Drop Ratio (RAN View)',
                  y_title='RRC Re-establishment & E-RAB Drop  (%)',
                  kpis=[('E_RAB Drop Ratio RAN View', 'Drop_Ratio', '(%)')]),
         ]),

    dict(id='D', name='Traffic', title='Traffic & Load',
         charts=[
             dict(sub='RRC Connection Setup Attempts',
                  y_title='RRC Connection Setup Attempts  (count)',
                  kpis=[('Total RRC Connection Setup Attempts', 'RRC_Attempts', '(count)')]),
             dict(sub='Average RRC Connected UEs',
                  y_title='Active UE Count  (avg)',
                  kpis=[('Average RRC Connected UEs', 'RRC_UEs', '(avg)')]),
             dict(sub='Average Active UEs with Data in Buffer — DL',
                  y_title='Active UE Count  (avg)',
                  kpis=[('Average Active UEs with data in the buffer DL',
                          'Active_UEs_DL', '(avg)')]),
             dict(sub='Average Active UEs with Data in Buffer — UL',
                  y_title='Active UE Count  (avg)',
                  kpis=[('Average Active UEs with data in the buffer UL',
                          'Active_UEs_UL', '(avg)')]),
             dict(sub='PDCP SDU Volume — DL',
                  y_title='PDCP SDU Volume DL  (bytes)',
                  kpis=[('PDCP SDU Volume DL', 'Vol_DL', '(bytes)')]),
             dict(sub='PDCP SDU Volume — UL',
                  y_title='PDCP SDU Volume UL  (bytes)',
                  kpis=[('PDCP SDU Volume UL', 'Vol_UL', '(bytes)')]),
         ]),

    dict(id='E', name='Handover', title='Handover Performance',
         charts=[
             dict(sub='Intra-eNB Handover Success Ratio',
                  y_title='Intra & Inter eNB Handover Success  (%)',
                  kpis=[('Total HO Success Ratio intra eNB', 'HO_Intra', '(%)')]),
             dict(sub='Inter-eNB X2 Handover Success Ratio',
                  y_title='Intra & Inter eNB Handover Success  (%)',
                  kpis=[('Total HO Success Ratio inter eNB X2 based', 'HO_X2', '(%)')]),
             dict(sub='Inter-eNB S1 Handover Success Ratio',
                  y_title='Intra & Inter eNB Handover Success  (%)',
                  kpis=[('Total HO Success Ratio inter eNB S1 based', 'HO_S1', '(%)')]),
             dict(sub='Inter-Frequency Handover Success Ratio',
                  y_title='Inter-Frequency & Inter-RAT Handover Success  (%)',
                  kpis=[('Inter_Frequency HO Success Ratio', 'HO_IF', '(%)')]),
             dict(sub='Inter-RAT Handover Success Ratio',
                  y_title='Inter-Frequency & Inter-RAT Handover Success  (%)',
                  kpis=[('Inter RAT Total HO Success Ratio', 'HO_IRAT', '(%)')]),
         ]),

    dict(id='F', name='Throughput', title='Throughput & Resource Utilisation',
         charts=[
             dict(sub='PDCP Active Cell Throughput DL',
                  y_title='PDCP Active Cell Throughput DL & UL  (Mbps)',
                  kpis=[('Average PDCP Layer Active Cell Throughput DL', 'Tput_DL', '(Mbps)')]),
             dict(sub='PDCP Active Cell Throughput UL',
                  y_title='PDCP Active Cell Throughput DL & UL  (Mbps)',
                  kpis=[('Average PDCP Layer Active Cell Throughput UL', 'Tput_UL', '(Mbps)')]),
             dict(sub='PRB Utilisation DL',
                  y_title='PRB Utilisation DL & UL  (%)',
                  kpis=[('Average PRB usage per TTI DL', 'PRB_DL', '(%)')]),
             dict(sub='PRB Utilisation UL',
                  y_title='PRB Utilisation DL & UL  (%)',
                  kpis=[('Average PRB usage per TTI UL', 'PRB_UL', '(%)')]),
         ]),

    dict(id='G', name='Quality', title='Radio Quality',
         charts=[
             dict(sub='Average CQI',
                  y_title='CQI',
                  kpis=[('Average CQI', 'CQI', '')]),
             dict(sub='Average CQI — 256QAM Configured UEs',
                  y_title='CQI (256QAM UEs)',
                  kpis=[('Average CQI of 256QAM configured UEs', 'CQI_256QAM', '')]),
             dict(sub='DL Residual Block Error Rate (rBLER)',
                  y_title='DL Block Error Rate  (%)',
                  kpis=[('Residual Block Error Rate_rBLER in DL', 'DL_BLER', '(%)')]),
             dict(sub='DL Initial BLER on PDSCH',
                  y_title='DL Initial BLER  (%)',
                  kpis=[('DL_SCH TB Failed Transmission Ratio_Initial BLER on PDSCH',
                          'DL_Init_BLER', '(%)')]),
             dict(sub='UL Residual Block Error Rate (rBLER)',
                  y_title='UL Block Error Rate  (%)',
                  kpis=[('Residual Block Error Rate_rBLER in UL', 'UL_BLER', '(%)')]),
             dict(sub='RLC PDU Retransmission Ratio — DL',
                  y_title='RLC PDU Retransmission Ratio  (%)',
                  kpis=[('RLC PDU Re_transmission Ratio Downlink', 'RLC_Retx_DL', '(%)')]),
             dict(sub='RLC PDU Retransmission Ratio — UL',
                  y_title='RLC PDU Retransmission Ratio  (%)',
                  kpis=[('RLC PDU Re_transmission Ratio Uplink', 'RLC_Retx_UL', '(%)')]),
             dict(sub='UL SINR — PUCCH & PUSCH',
                  y_title='UL SINR — PUCCH & PUSCH  (dB)',
                  kpis=[('Average SINR for PUCCH', 'SINR_PUCCH', '(dB)'),
                        ('Average SINR for PUSCH',  'SINR_PUSCH', '(dB)')]),
             dict(sub='Spectral Efficiency DL & UL',
                  y_title='Spectral Efficiency DL & UL  (bps/Hz)',
                  kpis=[('DL Spectral efficiency', 'SE_DL', '(bps/Hz)'),
                        ('UL Spectral efficiency', 'SE_UL', '(bps/Hz)')]),
         ]),

    dict(id='H', name='ENDC', title='EN-DC / 5G NSA Performance',
         charts=[
             dict(sub='SgNB Addition Success Ratio',
                  y_title='SgNB Addition Success Ratio  (%)',
                  kpis=[('Total SgNB Addition Success Ratio per SCG split bearer for Initial Access',
                          'SgNB_SR', '(%)')]),
             dict(sub='EN-DC Capable UEs',
                  y_title='EN-DC Capable UEs  (avg)',
                  kpis=[('Average number of UEs capable for EN_DC', 'ENDC_UEs', '(avg)')]),
         ]),

    dict(id='I', name='MCS_Radio', title='MCS & Radio Link Parameters',
         charts=[
             dict(sub='Average MCS — DL (PDSCH)',
                  y_title='Average MCS  (index)',
                  kpis=[('Average used MCS on PDSCH transmissions', 'MCS_DL', '')]),
             dict(sub='Average MCS — UL (PUSCH)',
                  y_title='Average MCS  (index)',
                  kpis=[('Average used MCS on PUSCH transmissions', 'MCS_UL', '')]),
             dict(sub='DL MCS Distribution — Low (<10) vs High (>19)',
                  y_title='DL MCS Distribution  (%)',
                  kpis=[('Percentage of PDSCH transmissions using Low MCS Codes_MCS LT 10',
                          'DL_MCS_Low', '(%)'),
                        ('Percentage of PDSCH transmissions using High MCS Codes_MCS GT 19',
                          'DL_MCS_High', '(%)')]),
             dict(sub='UL MCS Distribution — Low (<10) vs High (>19)',
                  y_title='UL MCS Distribution  (%)',
                  kpis=[('Percentage of PUSCH transmissions using Low MCS Codes_MCS LT 10',
                          'UL_MCS_Low', '(%)'),
                        ('Percentage of PUSCH transmissions using High MCS Codes_MCS GT 19',
                          'UL_MCS_High', '(%)')]),
             dict(sub='UE Power Headroom (PUSCH)',
                  y_title='UE Power Headroom  (dB)',
                  kpis=[('Avg UE power headroom for PUSCH from histogram PIs',
                          'PH_PUSCH', '(dB)')]),
             dict(sub='Percentage of UEs with Available UL Power',
                  y_title='UEs with UL Power Available  (%)',
                  kpis=[('Percentage of UEs with available Uplink Power',
                          'UL_Pwr_Avail', '(%)')]),
             dict(sub='Maximum Received Total Wideband Power (RTWP)',
                  y_title='RTWP  (dBm)',
                  kpis=[('Maximum received total wideband power RTWP', 'RTWP', '(dBm)')]),
             dict(sub='Average PDCCH Aggregation Level',
                  y_title='PDCCH AGG Level',
                  kpis=[('Average AGG level used for PDCCH scheduling', 'AGG_Level', '')]),
             dict(sub='PDCCH Aggregation Level Blocking Ratio',
                  y_title='AGG Level Blocking Ratio  (%)',
                  kpis=[('AGG level blocking ratio', 'AGG_Block', '(%)')]),
             dict(sub='Average Symbols Used in PDCCH',
                  y_title='PDCCH Symbols  (avg)',
                  kpis=[('Average number of symbols used in PDCCH', 'PDCCH_Sym', '')]),
         ]),

    dict(id='J', name='Latency', title='Latency & PDCP SDU Delay',
         charts=[
             dict(sub='Average Latency — DL',
                  y_title='Latency  (ms)',
                  kpis=[('Average Latency Downlink', 'Lat_DL', '(ms)')]),
             dict(sub='Average Latency — UL',
                  y_title='Latency  (ms)',
                  kpis=[('Average Latency Uplink', 'Lat_UL', '(ms)')]),
             dict(sub='PDCP SDU Delay DL — QCI 1 (VoIP)',
                  y_title='PDCP SDU Delay  (ms)',
                  kpis=[('Average PDCP SDU Delay in DL QCI1', 'SDU_QCI1', '(ms)')]),
             dict(sub='PDCP SDU Delay DL — QCI 5 (IMS Signalling)',
                  y_title='PDCP SDU Delay  (ms)',
                  kpis=[('Average PDCP SDU Delay in DL QCI5', 'SDU_QCI5', '(ms)')]),
             dict(sub='PDCP SDU Delay DL — QCI 8 (TCP)',
                  y_title='PDCP SDU Delay  (ms)',
                  kpis=[('Average PDCP SDU Delay in DL QCI8', 'SDU_QCI8', '(ms)')]),
             dict(sub='PDCP SDU Delay DL — QCI 9 (Best Effort)',
                  y_title='PDCP SDU Delay  (ms)',
                  kpis=[('Average PDCP SDU Delay in DL QCI9', 'SDU_QCI9', '(ms)')]),
         ]),
]

# ─── Aggregation ─────────────────────────────────────────────
def load_aggregate(fpath):
    """
    Load source file, filter to MNO carriers only,
    assign carrier label, aggregate daily by carrier.
    Returns DataFrame with columns: DATETIME, CARRIER, <kpi1>, <kpi2>, …
    """
    df = pd.read_excel(fpath, sheet_name=0, header=0)

    # Filter to MNO EARFCN only (drops NB-IoT rows and non-MNO carriers)
    df = df[df['EARFCN'].isin(MNO_EARFCN_MAP.keys())].copy()

    df['CARRIER']  = df['EARFCN'].map(MNO_EARFCN_MAP)
    df['DATETIME'] = pd.to_datetime(df['DATETIME'])

    kpis = [c for c in df.columns if c not in ('DATETIME','EARFCN','BAND','CARRIER')]
    agg  = {c: ('mean' if is_mean(c) else 'sum') for c in kpis}
    return df.groupby(['DATETIME','CARRIER']).agg(agg).reset_index()


def phase(dt):
    if dt < TRIAL_START:     return 'Pre-trial'
    if dt <= TRIAL_ROLLBACK: return 'Trial'
    return 'Post-rollback'


# ─── Chart dimensions ────────────────────────────────────────
CHART_W = 780   # pixels
CHART_H = 380   # pixels

# ─── Main workbook builder ───────────────────────────────────
def build(agg_df, carriers, rc, fname, out_path):
    """
    Build one Excel workbook.
    agg_df   : aggregated DataFrame (DATETIME, CARRIER, kpi…)
    carriers : ordered list of carrier labels present in data
    rc       : string label, e.g. 'RC3'
    fname    : source filename (for Cover sheet)
    out_path : output .xlsx path
    """
    wb = xlsxwriter.Workbook(out_path, {'nan_inf_to_errors': True})

    # ── Cell formats ────────────────────────────────────────
    fmt_hdr = wb.add_format({
        'bold': True, 'font_name': 'Arial', 'font_size': 9,
        'font_color': '#FFFFFF', 'bg_color': '#1F3864',
        'align': 'center', 'valign': 'vcenter', 'text_wrap': True, 'border': 0})
    fmt_date = wb.add_format({'num_format': 'DD-MMM-YYYY', 'font_name': 'Arial', 'font_size': 9})
    fmt_num  = wb.add_format({'font_name': 'Arial', 'font_size': 9, 'num_format': '#,##0.00'})
    fmt_str  = wb.add_format({'font_name': 'Arial', 'font_size': 9})

    # Phase-shaded row formats (created once per colour to avoid hitting format limit)
    _fmt_cache = {}
    def row_fmts(ph):
        if ph not in _fmt_cache:
            bg = '#FFFDE7' if ph == 'Trial' else ('#E3F2FD' if ph == 'Post-rollback' else None)
            if bg:
                _fmt_cache[ph] = (
                    wb.add_format({'num_format': 'DD-MMM-YYYY', 'font_name': 'Arial',
                                   'font_size': 9, 'bg_color': bg}),
                    wb.add_format({'font_name': 'Arial', 'font_size': 9,
                                   'num_format': '#,##0.00', 'bg_color': bg}),
                    wb.add_format({'font_name': 'Arial', 'font_size': 9, 'bg_color': bg}),
                )
            else:
                _fmt_cache[ph] = (fmt_date, fmt_num, fmt_str)
        return _fmt_cache[ph]

    fmt_title  = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 18,
        'font_color': '#FFFFFF', 'bg_color': '#1F3864', 'align': 'center', 'valign': 'vcenter'})
    fmt_lbl    = wb.add_format({'bold': True,  'font_name': 'Arial', 'font_size': 10})
    fmt_val    = wb.add_format({'font_name': 'Arial', 'font_size': 10})
    fmt_sub    = wb.add_format({'italic': True, 'font_name': 'Arial', 'font_size': 8,
                                 'font_color': '#555555'})
    fmt_ctitle = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 14,
                                 'font_color': '#1F3864'})
    fmt_clbl   = wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10,
                                 'font_color': '#2F5496'})

    carrier_fmts = {c: wb.add_format({'bold': True, 'font_name': 'Arial', 'font_size': 10,
                                       'font_color': CARRIER_COLORS.get(c, '#888888')})
                    for c in CARRIER_ORDER}

    dates = sorted(agg_df['DATETIME'].unique())
    n     = len(dates)

    # ── Cover sheet ──────────────────────────────────────────
    wc = wb.add_worksheet('Cover')
    wc.hide_gridlines(2)
    wc.set_column('A:A', 46); wc.set_column('B:B', 54)
    wc.set_row(0, 52)
    wc.merge_range('A1:B1', f'4G KPI Performance Report — {rc}', fmt_title)

    meta = [
        ('Source file:',            fname,                                              None),
        ('Trial feature:',          'Nokia 4G Energy Saving — Power Saving Mode',       None),
        ('Trial implementation:',   TRIAL_START.strftime('%d %B %Y'),                                 None),
        ('Trial rollback:',         TRIAL_ROLLBACK.strftime('%d %B %Y') if TRIAL_ROLLBACK else 'n/a',                                    None),
        ('Data period:',            '<YYYY-MM-DD → YYYY-MM-DD> (daily)',                None),
        ('Carrier filter:',         'MNO carriers only (see references/lte/carrier_allocation.md)',     None),
        ('Aggregation:',            'Counters → SUM per carrier;  Ratios → MEAN per carrier', None),
        ('NB-IoT / non-MNO rows:',  'Excluded before aggregation',                      None),
        ('', '', None),
        ('Report structure:',       '10 KPI groups × 2 sheets (C-tab = charts; D-tab = data, hidden)', None),
        ('', '', None),
        ('Row shading (D-tabs):',   '', None),
        ('', 'Yellow  = Trial active (baseline end → rollback)', None),
        ('', 'Blue    = Post-rollback (rollback date onwards)', None),
        ('', '', None),
        ('Chart markers:',          '', None),
        ('', 'Red bar   = Trial implementation date', None),
        ('', 'Blue bar  = Trial rollback date', None),
        ('', '(Secondary Y axis 0–1 on right side)', None),
        ('', '', None),
        ('D-tabs (raw data):',      'Hidden — right-click sheet tab → Unhide to access', None),
        ('', '', None),
        ('Carriers in this file:',  '', None),
    ]
    for c in carriers:
        meta.append(('', f'  {c}', c))

    for i, (lbl, val, carrier) in enumerate(meta, start=1):
        wc.set_row(i, 16)
        wc.write(i, 0, lbl, fmt_lbl if lbl else fmt_val)
        if carrier and carrier in carrier_fmts:
            wc.write(i, 1, val, carrier_fmts[carrier])
        else:
            wc.write(i, 1, val, fmt_val)

    # ── Master aggregate data sheet ──────────────────────────
    wp = wb.add_worksheet('Agg_Data')
    wp.freeze_panes(1, 2)
    agg_cols = [c for c in agg_df.columns if c not in ('DATETIME','CARRIER')]
    hdr_agg  = ['Date', 'Carrier'] + agg_cols
    wp.set_row(0, 42)
    for ci, h in enumerate(hdr_agg):
        wp.write(0, ci, h, fmt_hdr)
    wp.set_column(0, 0, 13); wp.set_column(1, 1, 12)

    for ri, (_, row) in enumerate(
            agg_df.sort_values(['DATETIME','CARRIER']).iterrows(), start=1):
        ph   = phase(row['DATETIME'])
        fd, fn, fs = row_fmts(ph)
        wp.write_datetime(ri, 0, row['DATETIME'].to_pydatetime(), fd)
        wp.write(ri, 1, row['CARRIER'], fs)
        for ci, c in enumerate(agg_cols, start=2):
            v = row[c]
            if isinstance(v, float) and np.isnan(v):
                wp.write_blank(ri, ci, None, fn)
            else:
                wp.write_number(ri, ci,
                                float(v) if isinstance(v, (np.floating, float)) else int(v), fn)

    # ── KPI group sheets ─────────────────────────────────────
    for mg in META_GROUPS:
        # Collect all KPIs across all charts in this group, check availability
        all_kpis = [(col, sh, un, ci, ki)
                    for ci, chart in enumerate(mg['charts'])
                    for ki, (col, sh, un) in enumerate(chart['kpis'])]
        avail_kpis = [(col, sh, un, ci, ki) for (col, sh, un, ci, ki) in all_kpis
                      if col in agg_df.columns and not agg_df[col].isna().all()]
        if not avail_kpis:
            continue

        d_name = f'D_{mg["name"]}'[:31]
        c_name = f'C_{mg["name"]}'[:31]

        # ── D-tab (data sheet) ───────────────────────────────
        ds = wb.add_worksheet(d_name)
        ds.freeze_panes(1, 1)
        ds.set_column(0, 0, 13)
        ds.set_row(0, 42)

        hdr_d   = ['Date']
        col_map = {}   # col_map[chart_idx][kpi_idx][carrier] = 0-based col index
        cursor  = 1

        for col, sh, un, ci, ki in avail_kpis:
            if ci not in col_map:        col_map[ci] = {}
            if ki not in col_map[ci]:    col_map[ci][ki] = {}
            for carrier in carriers:
                hdr_d.append(f'{sh}_{carrier}')
                col_map[ci][ki][carrier] = cursor
                ds.set_column(cursor, cursor, 12)
                cursor += 1

        trial_col  = cursor; hdr_d.append('Trial_Start'); cursor += 1
        rollbk_col = cursor; hdr_d.append('Rollback');    cursor += 1
        phase_col  = cursor; hdr_d.append('Phase');       cursor += 1
        ncols      = cursor

        for ci2, h in enumerate(hdr_d):
            ds.write(0, ci2, h, fmt_hdr)

        for ri, dt in enumerate(dates, start=1):
            ph = phase(dt)
            fd, fn, fs = row_fmts(ph)
            ds.write_datetime(ri, 0, dt.to_pydatetime(), fd)

            for col, sh, un, ci, ki in avail_kpis:
                for carrier in carriers:
                    mask = (agg_df['DATETIME'] == dt) & (agg_df['CARRIER'] == carrier)
                    sub  = agg_df.loc[mask, col]
                    val  = float(sub.iloc[0]) if (len(sub) > 0 and not sub.isna().all()) else None
                    c_i  = col_map[ci][ki][carrier]
                    if val is None or (isinstance(val, float) and np.isnan(val)):
                        ds.write_blank(ri, c_i, None, fn)
                    else:
                        ds.write_number(ri, c_i, val, fn)

            ds.write_number(ri, trial_col,  1.0 if dt == TRIAL_START    else 0.0, fn)
            ds.write_number(ri, rollbk_col, 1.0 if dt == TRIAL_ROLLBACK else 0.0, fn)
            ds.write(ri, phase_col, ph, fs)

        # Conditional formatting — phase colouring
        last_ltr = xu.xl_col_to_name(ncols - 1)
        ph_ltr   = xu.xl_col_to_name(phase_col)
        ds.conditional_format(f'A2:{last_ltr}{n+1}', {
            'type': 'formula',
            'criteria': f'=${ph_ltr}2="Trial"',
            'format': wb.add_format({'bg_color': '#FFFDE7'})})
        ds.conditional_format(f'A2:{last_ltr}{n+1}', {
            'type': 'formula',
            'criteria': f'=${ph_ltr}2="Post-rollback"',
            'format': wb.add_format({'bg_color': '#E3F2FD'})})

        # Hide D-tab — accessible via right-click → Unhide
        ds.hide()

        # ── C-tab (chart sheet) ──────────────────────────────
        cs = wb.add_worksheet(c_name)
        cs.hide_gridlines(2)
        cs.set_column('A:A', 4)
        cs.set_row(0, 26); cs.set_row(1, 14)
        cs.write(0, 0, f'{rc}  │  {mg["title"]}', fmt_ctitle)
        cs.write(1, 0,
                 'Trial start  │  Rollback  │  '
                 'Red bar = Trial start  │  Blue bar = Rollback  │  '
                 'Yellow/blue row shading in D-tab (hidden — right-click tab → Unhide)',
                 fmt_sub)

        row_anchor = 2   # 0-indexed Excel row where next item is placed

        # Determine which chart_idxs have available KPIs
        charts_avail = {}
        for col, sh, un, ci, ki in avail_kpis:
            if ci not in charts_avail:
                charts_avail[ci] = []
            charts_avail[ci].append((col, sh, un, ki))

        for ci in sorted(charts_avail.keys()):
            chart_def   = mg['charts'][ci]
            kpi_entries = charts_avail[ci]

            # Section label row
            cs.set_row(row_anchor, 16)
            cs.write(row_anchor, 0, f'  {chart_def["sub"]}', fmt_clbl)
            row_anchor += 1

            # Line chart
            lc = wb.add_chart({'type': 'line'})
            lc.set_size({'width': CHART_W, 'height': CHART_H})
            lc.set_legend({'position': 'right'})
            lc.set_x_axis({'date_axis': True, 'num_format': 'dd-mmm',
                           'major_unit': 7, 'major_unit_type': 'days'})
            lc.set_y_axis({'name': chart_def['y_title'], 'num_format': '#,##0.00'})
            lc.set_y2_axis({'min': 0, 'max': 1, 'num_format': ';;;',
                            'major_gridlines': {'visible': False}})

            for col, sh, un, ki in kpi_entries:
                for carrier in carriers:
                    c_i = col_map[ci][ki][carrier]
                    lc.add_series({
                        'name':       [d_name, 0, c_i],
                        'categories': [d_name, 1, 0, n, 0],
                        'values':     [d_name, 1, c_i, n, c_i],
                        'line': {'color': CARRIER_COLORS.get(carrier, '#888888'),
                                 'width': 1.5},
                        'marker': {'type': 'none'},
                    })

            # Bar chart for trial markers (secondary Y axis, 0–1)
            bc = wb.add_chart({'type': 'column'})
            bc.add_series({
                'name':       [d_name, 0, trial_col],
                'categories': [d_name, 1, 0, n, 0],
                'values':     [d_name, 1, trial_col, n, trial_col],
                'fill':   {'color': '#CC0000', 'transparency': 20},
                'border': {'none': True},
                'y2_axis': True,
            })
            bc.add_series({
                'name':       [d_name, 0, rollbk_col],
                'categories': [d_name, 1, 0, n, 0],
                'values':     [d_name, 1, rollbk_col, n, rollbk_col],
                'fill':   {'color': '#0000CC', 'transparency': 20},
                'border': {'none': True},
                'y2_axis': True,
            })

            lc.combine(bc)
            cs.insert_chart(row_anchor, 0, lc, {'x_offset': 5, 'y_offset': 5})
            row_anchor += 22

    wb.close()
    print(f'  Saved → {out_path}')


# ─── Main ────────────────────────────────────────────────────
FILES = {
    'RC3': './4G_System_Program_Nokia_<dates>_RC3.xlsx'   # ← EDIT,
    'RC4': './4G_System_Program_Nokia_<dates>_RC4.xlsx'   # ← EDIT,
}

for rc, fpath in FILES.items():
    print(f'\n{"="*55}\nProcessing {rc} …')
    agg      = load_aggregate(fpath)
    carriers = [c for c in CARRIER_ORDER if c in agg['CARRIER'].values]
    print(f'  MNO carriers found: {carriers}')
    print(f'  Dates: {agg["DATETIME"].nunique()}')

    # Verify no >100% ratio issue for B2300 (spot check ERAB_Init)
    if 'Initial E_RAB Accessibility' in agg.columns:
        for car in ['B2300_F1', 'B2300_F2']:
            if car in agg['CARRIER'].values:
                mx = agg.loc[agg['CARRIER'] == car, 'Initial E_RAB Accessibility'].max()
                print(f'  ERAB_Init max for {car}: {mx:.2f}%  (should be ≤100%)')

    out = f'./{rc}_KPI_Grouped.xlsx'
    build(agg, carriers, rc, fpath.split('/')[-1], out)

print('\n✓ Done.')
