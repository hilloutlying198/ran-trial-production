"""
build_stats_report_nr.py — NR Statistical Analysis per RC
==========================================================
Generates one Statistical_Analysis Excel per RC.
Computes all statistics directly from raw Nokia export files (no manual arrays).
Supports:
  - SUBNETWORK filter for per-RC processing
  - 3-phase support: Baseline / Trial / Post-RB (Post-RB omitted when TRIAL_ROLLBACK is None)
  - ES data filtered per RC
  - KPI_Trajectories via feature_context.json
"""
import warnings; warnings.filterwarnings('ignore')
import json, os, sys
import pandas as pd
import numpy as np
import xlsxwriter
import xlsxwriter.utility as xu

# =============================================================================
# CONFIGURATION
# =============================================================================
TRIAL_ID   = 'CBXXXXXX'                            # ← EDIT: your trial ID
RCS        = ['RC3', 'RC4']                          # ← EDIT: your RC labels

BASELINE_START = pd.Timestamp('YYYY-MM-DD')          # ← EDIT
BASELINE_END   = pd.Timestamp('YYYY-MM-DD')          # ← EDIT
TRIAL_START    = pd.Timestamp('YYYY-MM-DD')          # ← EDIT
TRIAL_END      = pd.Timestamp('YYYY-MM-DD')          # ← EDIT
TRIAL_ROLLBACK = pd.Timestamp('YYYY-MM-DD')          # ← EDIT: or None if no rollback
POST_RB_START  = pd.Timestamp('YYYY-MM-DD')          # ← EDIT: first day after rollback (or None)
POST_RB_END    = pd.Timestamp('YYYY-MM-DD')          # ← EDIT: last day of post-RB window (or None)

CARRIER_ORDER  = ['N28', 'N78_F1', 'N78_F2', 'N78_F3']          # ← EDIT
CARRIER_COLORS = {'N28': '#D62728', 'N78_F1': '#1F77B4', 'N78_F2': '#2CA02C', 'N78_F3': '#9467BD'}  # ← EDIT
MNO_NR_NRARFCN_MAP = {152600: 'N28', 635334: 'N78_F1', 650666: 'N78_F2', 652000: 'N78_F3'}          # ← EDIT

MAIN_FILE = './5G_System_Program_Nokia_per_RC_per_carrier.xlsx'   # ← EDIT: your KPI export file name
ES_FILE   = './5G_ES_Nokia_per_RC.xlsx'                           # ← EDIT: your ES export file name
OUT_DIR   = './'                                                  # ← EDIT: output directory
FC_PATH   = './feature_context.json'                              # ← EDIT: path to feature_context.json

# =============================================================================
# KPI COLUMN MAP (Nokia column → display name, tier, higher_bad)
# =============================================================================
NR_COLUMN_MAP = {
    'Cell in Reduced TX Power Saving Mode Ratio':                     ('ReducedTX Ratio',       'T1-ES',      False),
    'DRX sleep time ratio':                                           ('DRX Sleep Ratio',        'T1-ES',      False),
    'Usage ratio of PDSCH data slots over all DL data slots':         ('PDSCH Slot Usage',       'T1-ES',      False),
    'Average delay DL in CU_UP per cell':                             ('Avg DL Delay CU-UP',     'T1-Lat',     True),
    'Average MAC layer user throughput in downlink':                  ('Avg MAC Tput DL',        'T1-Tput',    False),
    'Average PDCP re_ordering delay in the UL per cell':              ('Avg UL Reorder Delay',   'T2',         True),
    'Average wideband CQI 64QAM table':                               ('Avg CQI 64QAM',          'T2',         False),
    'Average wideband CQI 256QAM table':                              ('Avg CQI 256QAM',         'T2',         False),
    'Average UE related SINR for PUSCH in Rank 1':                    ('Avg SINR PUSCH R1',      'T2',         False),
    'Average UE related SINR for PUSCH in Rank 2':                    ('Avg SINR PUSCH R2',      'T2',         False),
    'Average UE related SINR for PUCCH':                              ('Avg SINR PUCCH',         'T2',         False),
    'Average UE power headroom for PUSCH calculated from histogram counters': ('Avg PHR PUSCH',  'T2',         False),
    'Average UE pathloss level for PUSCH':                            ('Avg Pathloss PUSCH',     'T2',         True),
    'Maximum DL PDCP SDU NR leg throughput per DRB':                  ('Max DL PDCP Tput',       'T2',         False),
    'Maximum MAC SDU Cell Throughput in DL on DTCH':                  ('Max Cell Tput DL',       'T2',         False),
    'Maximum MAC SDU Cell Throughput in UL on DTCH':                  ('Max Cell Tput UL',       'T2',         False),
    'Average MCS used in downlink for PDSCH with 64QAM table':        ('Avg MCS DL 64QAM',       'T2',         False),
    'Average MCS used in downlink for PDSCH with 256QAM table':       ('Avg MCS DL 256QAM',      'T2',         False),
    'Average rank used in downlink':                                  ('Avg DL Rank',            'T2',         False),
    'Average MCS used in uplink for PUSCH with 64QAM table':          ('Avg MCS UL 64QAM',       'T2',         False),
    'PRB utilization for PDSCH':                                      ('PRB Util DL',            'T2',         False),
    'PRB utilization for PUSCH':                                      ('PRB Util UL',            'T2',         False),
    'Usage ratio of PUSCH data slots over all UL data slots':         ('PUSCH Slot Usage',       'T2',         False),
    'Average aggregation level used on PDCCH uplink grants':          ('Avg PDCCH AGG UL',       'T2',         False),
    'Average aggregation level used on PDCCH downlink grants':        ('Avg PDCCH AGG DL',       'T2',         False),
    'Admission control rejection ratio due to lack of PUCCH resources':   ('PUCCH Rej NSA',      'T2',         True),
    'Admission control rejection ratio due to lack of PUCCH resources.1': ('PUCCH Rej SA',       'T2',         True),
    'Cell availability ratio':                                        ('Cell Availability',      'T3',         False),
    'Cell availability ratio excluding planned unavailability periods':('Cell Avail (excl)',      'T3',         False),
    'Accessibility success ratio':                                    ('Accessibility SR',       'T3',         False),
    'Initial UE message sent success ratio':                          ('Init UE Msg SR',         'T3',         False),
    'NGAP connection establishment success ratio':                    ('NGAP Setup SR',          'T3',         False),
    'QoS Flow Setup Success Ratio':                                   ('QoS Flow Setup SR',      'T3',         False),
    'Non_Stand Alone call accessibility 5G side':                     ('NSA Call Access SR',     'T3',         False),
    'RRC connection establishment success ratio':                     ('RRC Setup SR',           'T3',         False),
    'Initial E_RAB Setup Success Ratio':                              ('Init E-RAB SR',          'T3',         False),
    'UE context setup success ratio':                                 ('UE Ctx Setup SR',        'T3',         False),
    'Radio admission success ratio for NSA user':                     ('Radio Admission NSA',    'T3',         False),
    'Radio admission success ratio for SA users':                     ('Radio Admission SA',     'T3',         False),
    'Active RACH setup success ratio':                                ('Active RACH SR',         'T3',         False),
    'Contention based RACH setup success ratio':                      ('CB RACH SR',             'T3',         False),
    'Contention free RACH setup success ratio':                       ('CF RACH SR',             'T3',         False),
    'SgNB addition preparation success ratio':                        ('SgNB Add Prep SR',       'T3',         False),
    'SgNB reconfiguration success ratio':                             ('SgNB Reconfig SR',       'T3',         False),
    'Status Transfer failure ratio during SgNB Addition':             ('SgNB Xfer Fail',         'T3',         True),
    'QoS Flow Drop Ratio _ RAN view':                                 ('QoS Flow Drop RAN',      'T3',         True),
    'QoS Flow Drop Ratio _ User view_double_Ng mapped to UE lost':    ('QoS Flow Drop UEL',      'T3',         True),
    'Active QoS Flow Drop Ratio_double_Ng mapped to UE lost':         ('Active QoS Drop',        'T3',         True),
    'Active E_RAB Drop Ratio _ SgNB view':                            ('Active E-RAB Drop',      'T3',         True),
    'SgNB triggered abnormal release ratio excluding X2 reset':       ('SgNB Abn Release',       'T3',         True),
    'Ratio of SgNB releases initiated by SgNB due to radio connection with UE lost': ('SgNB Rel UEL', 'T3',  True),
    'Ratio of UE releases due to abnormal reasons':                   ('UE Abn Release',         'T3',         True),
    'Number of UE releases due to radio link failure':                ('RLF UE Rel',             'T3',         True),
    'Number of UE redirections to E_UTRAN due to voice fallback to LTE': ('EPS Fallback',        'T3',         True),
    'Intra_frequency Intra_gNB Intra_DU handover total success ratio':  ('Intra-DU IF HO SR',   'T3',         False),
    'Intra_gNB Intra_DU Inter_frequency HO total success ratio per PLMN': ('Intra-DU XF HO SR', 'T3',         False),
    'Intra_frequency Xn based Inter_gNB handover execution success ratio per PLMN': ('Xn Inter-gNB HO SR','T3',False),
    'Xn based Inter_gNB Inter_frequency HO execution success ratio per PLMN': ('Xn Inter-gNB XF HO SR','T3',False),
    'Inter gNB handover success ratio for NSA':                       ('Inter-gNB HO NSA',       'T3',         False),
    'Inter_frequency intra_DU handover total success ratio for NSA':  ('XF Intra-DU HO NSA',    'T3',         False),
    'Intra_frequency intra_DU PSCell change preparation success ratio':('PSCell Chg Prep SR',    'T3',         False),
    'Intra_frequency intra_DU PSCell change total success ratio':     ('PSCell Chg SR',          'T3',         False),
    'Downlink carrier aggregation reconfiguration success ratio':     ('DL CA Reconfig SR',      'T3',         False),
    'Average PDCCH CCE starvation ratio in cell':                     ('PDCCH Starvation',       'T3',         True),
    'Average number of active UEs with data in the buffer for DRBs in DL': ('Avg Active DL UEs', 'T4-Traffic', False),
    'Average number of active UEs with data in the buffer for DRBs in UL': ('Avg Active UL UEs', 'T4-Traffic', False),
    'Average number of NSA users in selected area':                   ('Avg NSA Users',          'T4-Traffic', False),
    'Average number of SA RRC connected users in selected area':      ('Avg SA RRC Users',       'T4-Traffic', False),
    'MAC SDU data volume transmitted in DL on DTCH':                  ('DL Data Volume',         'T4-Traffic', False),
    'MAC SDU data volume received in UL on DTCH':                     ('UL Data Volume',         'T4-Traffic', False),
}

NR_ES_COLUMN_MAP = {
    '[N]RU_ENERGY_CONSUMPTION':     ('RU Energy Consumption', 'T1-ES', True),
    '[N]RU_AVG_PWR_USAGE':          ('RU Avg Power Usage',    'T1-ES', True),
    '[N]RU_MAX_PWR_USAGE':          ('RU Max Power Usage',    'T2',    True),
    '[N]RU_MIN_PWR_USAGE':          ('RU Min Power Usage',    'T2',    True),
    '[N]ENERGY_CONSUMPTION_IN_SM':  ('System Module Energy',  'T1-ES', True),
    '[N]ENERGY_CONSUMPTION_IN_RF':  ('RF Energy',             'T1-ES', True),
    '[N]ENERGY_CONSUMPTION_IN_BTS': ('Total BTS Energy',      'T1-ES', True),
    '[N]MAX_INPUT_VOLTAGE_IN_RF':   ('Max RF Input Voltage',  'T4-Traffic', False),
}

PER_CARRIER_KPIS = [
    'Cell in Reduced TX Power Saving Mode Ratio',
    'DRX sleep time ratio',
    'Usage ratio of PDSCH data slots over all DL data slots',
    'Average delay DL in CU_UP per cell',
    'Average MAC layer user throughput in downlink',
    'Average PDCCH CCE starvation ratio in cell',
]

MEAN_KW = ['ratio','rate','efficiency','average','cqi','sinr','rssi','bler','mcs',
           'percentage','maximum','latency','delay','usage','level','avg','pathloss',
           'rank','starvation','sleep','reduced','availability','admission','utilization',
           'utilisation','aggregation','drop','abnormal','release','headroom']
SUM_KW  = ['number of','attempts','data volume','requests','releases','redirections']

def is_mean(col):
    low = col.lower()
    for kw in SUM_KW:
        if kw in low: return False
    for kw in MEAN_KW:
        if kw in low: return True
    return True

TIER_COLORS = {
    'T1-ES': '#E2EFDA', 'T1-Lat': '#DAEEF3', 'T1-Tput': '#FFF2CC',
    'T2': '#F2F2F2', 'T3': '#FFFFFF', 'T4-Traffic': '#EDE7F6',
}

# =============================================================================
# DATA LOADING
# =============================================================================
def load_main_rc(rc_label):
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
    return df

def load_es_rc(rc_label):
    df = pd.read_excel(ES_FILE, engine='openpyxl')
    df.columns = df.columns.str.strip()
    dt_col = next((c for c in df.columns if c.upper() in ('DATETIME','DATE','PERIOD START TIME')), df.columns[0])
    df = df.rename(columns={dt_col: 'DATETIME'})
    df['DATETIME'] = pd.to_datetime(df['DATETIME'], errors='coerce').dt.normalize()
    df = df.dropna(subset=['DATETIME'])
    if 'SUBNETWORK' in df.columns:
        df = df[df['SUBNETWORK'] == rc_label].copy()
    return df

# =============================================================================
# STATISTICS COMPUTATION
# =============================================================================
def compute_stats(df, kpi_cols, bl_mask, tr_mask, pr_mask=None, groupby='DATETIME'):
    rows = []
    for c in kpi_cols:
        if c not in df.columns: continue
        try:
            agg_fn = 'mean' if is_mean(c) else 'sum'
            bl_d = df[bl_mask].groupby(groupby)[c].agg(agg_fn).dropna()
            tr_d = df[tr_mask].groupby(groupby)[c].agg(agg_fn).dropna()
            if len(bl_d)==0 or len(tr_d)==0: continue
            bl_mean = float(bl_d.mean()); tr_mean = float(tr_d.mean())
            bl_std  = float(bl_d.std(ddof=1)) if len(bl_d)>1 else None
            pr_mean = None
            if pr_mask is not None:
                pr_d = df[pr_mask].groupby(groupby)[c].agg(agg_fn).dropna()
                if len(pr_d): pr_mean = float(pr_d.mean())
            sigma = round((tr_mean-bl_mean)/bl_std, 2) if (bl_std and bl_std>1e-9) else None
            rows.append({'col':c,'bl':round(bl_mean,4),'tr':round(tr_mean,4),
                         'pr':round(pr_mean,4) if pr_mean is not None else None,
                         'sigma':sigma,'bl_std':bl_std,'n_bl':len(bl_d),'n_tr':len(tr_d)})
        except Exception as e:
            print(f'  [warn] {c}: {e}', file=sys.stderr)
    return rows

def chart_sigma(sigma, higher_bad):
    if sigma is None: return None
    return sigma if higher_bad else -sigma

def sigma_colour(cs_val):
    if cs_val is None: return '#E0E0E0'
    s = abs(cs_val)
    if s>=3.0: return '#C00000' if cs_val>0 else '#006100'
    if s>=2.0: return '#E97132' if cs_val>0 else '#548235'
    if s>=1.0: return '#FFC000' if cs_val>0 else '#9BC2E6'
    return '#F0F0F0'

# =============================================================================
# FEATURE CONTEXT
# =============================================================================
def load_feature_context():
    if not os.path.exists(FC_PATH):
        print(f'[warn] feature_context.json not found at {FC_PATH} — KPI_Trajectories skipped')
        return None
    with open(FC_PATH, encoding='utf-8') as f:
        ctx = json.load(f)
    t1 = [(k['col'],k['label'],k['unit'],k.get('category','')) for k in ctx.get('t1_carrier_kpis',[])]
    es = [(k['col'],k['label'],k['unit']) for k in ctx.get('t1_es_kpis',[])]
    print(f'  Feature context: {ctx.get("feature_name","")} ({ctx.get("feature_doc","")})')
    print(f'  T1 carrier KPIs: {len(t1)}   T1 ES KPIs: {len(es)}')
    return {'t1':t1,'es':es,'name':ctx.get('feature_name',''),'doc':ctx.get('feature_doc',''),
            'mechanism':ctx.get('mechanism_summary','')}

# =============================================================================
# WORKBOOK BUILD
# =============================================================================
def build_workbook(rc_label, df, es_df, carriers, feat_ctx, out_path):
    wb = xlsxwriter.Workbook(out_path, {'nan_inf_to_errors': True})

    # Period masks
    bl_mask = (df['DATETIME']>=BASELINE_START)&(df['DATETIME']<=BASELINE_END)
    tr_mask = (df['DATETIME']>=TRIAL_START)   &(df['DATETIME']<=TRIAL_END)
    pr_mask = ((df['DATETIME']>=POST_RB_START)&(df['DATETIME']<=POST_RB_END)
               if POST_RB_START is not None else pd.Series(False, index=df.index))

    es_bl = (es_df['DATETIME']>=BASELINE_START)&(es_df['DATETIME']<=BASELINE_END)
    es_tr = (es_df['DATETIME']>=TRIAL_START)   &(es_df['DATETIME']<=TRIAL_END)
    es_pr = ((es_df['DATETIME']>=POST_RB_START)&(es_df['DATETIME']<=POST_RB_END)
             if POST_RB_START is not None else pd.Series(False, index=es_df.index))

    # Compute stats
    kpi_cols = [c for c in NR_COLUMN_MAP if c in df.columns]
    feat_stats = compute_stats(df, kpi_cols, bl_mask, tr_mask, pr_mask)
    feat_by_name = {NR_COLUMN_MAP[r['col']][0]: r for r in feat_stats}

    es_cols = [c for c in NR_ES_COLUMN_MAP if c in es_df.columns]
    es_df2 = es_df.copy(); es_df2['DATETIME'] = es_df2['DATETIME']
    es_stats = compute_stats(es_df2, es_cols, es_bl, es_tr, es_pr)
    es_by_name = {NR_ES_COLUMN_MAP[r['col']][0]: r for r in es_stats}

    # Per-carrier stats
    pc_data = {}
    for carrier in carriers:
        c_mask = df['CARRIER']==carrier
        rows = compute_stats(df[c_mask], PER_CARRIER_KPIS,
                             bl_mask&c_mask, tr_mask&c_mask, pr_mask&c_mask)
        pc_data[carrier] = {r['col']: r for r in rows}

    # ── Formats ──────────────────────────────────────────────────────────────
    fmt_title = wb.add_format({'bold':True,'font_name':'Arial','font_size':14,'font_color':'#1F3864'})
    fmt_sub   = wb.add_format({'italic':True,'font_name':'Arial','font_size':9,'font_color':'#555555'})
    fmt_hdr   = wb.add_format({'bold':True,'font_name':'Arial','font_size':9,
                                'bg_color':'#1F3864','font_color':'white',
                                'align':'center','valign':'vcenter','text_wrap':True,'border':1})
    fmt_lbl   = wb.add_format({'font_name':'Arial','font_size':9,'border':1})
    fmt_num   = wb.add_format({'font_name':'Arial','font_size':9,'num_format':'#,##0.00','border':1})
    fmt_sigma = wb.add_format({'font_name':'Arial','font_size':9,'num_format':'+0.00;-0.00;0.00','border':1,'align':'center'})
    fmt_meta_lbl = wb.add_format({'bold':True,'font_name':'Arial','font_size':10})
    fmt_meta_val = wb.add_format({'font_name':'Arial','font_size':10})
    fmt_ctitle = wb.add_format({'bold':True,'font_name':'Arial','font_size':14,'font_color':'#1F3864'})
    fmt_clbl   = wb.add_format({'bold':True,'font_name':'Arial','font_size':10,'font_color':'#2F5496'})

    def tier_fmt(tier):
        bg = TIER_COLORS.get(tier,'#FFFFFF')
        return wb.add_format({'font_name':'Arial','font_size':9,'border':1,'bg_color':bg,'bold':True})

    def sigma_fmt(cs_val):
        bg = sigma_colour(cs_val)
        fc = '#FFFFFF' if (cs_val is not None and abs(cs_val)>=2.0) else '#000000'
        return wb.add_format({'font_name':'Arial','font_size':9,'num_format':'+0.00;-0.00;0.00',
                               'border':1,'align':'center','bg_color':bg,'font_color':fc})

    # ── Sheet 1: Overview ─────────────────────────────────────────────────────
    print('  Building Overview …')
    ov = wb.add_worksheet('Overview')
    ov.hide_gridlines(2)
    ov.set_column('A:A',30); ov.set_column('B:B',50)
    ov.merge_range('A1:B1', f'{TRIAL_ID} NR NSA Statistical Analysis — {rc_label}', fmt_title)
    post_rb_str = (f'{POST_RB_START.strftime("%d %b %Y")} → {POST_RB_END.strftime("%d %b %Y")}'
                   if POST_RB_START is not None else 'n/a (no rollback)')
    meta = [
        ('Trial ID:',          TRIAL_ID),
        ('RC:',                rc_label),
        ('Feature:',           '<feature name>'),                      # ← EDIT
        ('Feature doc:',       '<feature document reference>'),        # ← EDIT
        ('Technology:',        'NR NSA (EN-DC)'),
        ('Baseline:',          f'{BASELINE_START.strftime("%d %b %Y")} → {BASELINE_END.strftime("%d %b %Y")}'),
        ('Trial:',             f'{TRIAL_START.strftime("%d %b %Y")} → {TRIAL_END.strftime("%d %b %Y")}'),
        ('Post-RB:',           post_rb_str),
        ('Carriers:',          ', '.join(carriers)),
        ('Parameters:',        '<parameter name>=<value>; ...'),       # ← EDIT
        ('Mechanism:',         '<brief feature mechanism summary>'),   # ← EDIT
        ('H0 note:',           'Feature activated on ALL NR carriers simultaneously — no internal control group. Baseline-vs-trial comparison only.'),
        ('Concurrent effects:','Concurrent network changes cannot be distinguished from feature effects using in-cluster data alone.'),
        ('',                   ''),
        ('Sigma convention:',  'Degradation-positive: positive sigma = worse (for charts); raw sigma = (trial-baseline)/baseline_std'),
        ('Colour thresholds:','≥3σ = red/green (high significance); ≥2σ = orange/teal; ≥1σ = yellow/blue; <1σ = grey'),
    ]
    for i,(lbl,val) in enumerate(meta, start=1):
        ov.set_row(i,22)
        ov.write(i,0,lbl,fmt_meta_lbl if lbl else fmt_meta_val)
        ov.write(i,1,val,fmt_meta_val)

    # ── Sheet 2: Significance Matrix ──────────────────────────────────────────
    print('  Building Significance_Matrix …')
    sm = wb.add_worksheet('Significance_Matrix')
    sm.freeze_panes(1,1)
    sm.set_column('A:A',22)
    for ci,h in enumerate(['KPI','Tier','Baseline','Trial','Post-RB','Δ%','σ (raw)','σ (chart)','Sign. level']):
        sm.write(0,ci,h,fmt_hdr)
        sm.set_column(ci,ci,14 if ci==0 else 11)

    feat_rows_ordered = sorted(feat_stats, key=lambda r: (
        {'T1-ES':0,'T1-Lat':1,'T1-Tput':2,'T2':3,'T3':4,'T4-Traffic':5}.get(NR_COLUMN_MAP.get(r['col'],('','T3',''))[1],'T3'), 0))

    for ri, r in enumerate(feat_rows_ordered, start=1):
        col = r['col']
        if col not in NR_COLUMN_MAP: continue
        name, tier, hib = NR_COLUMN_MAP[col]
        cs = chart_sigma(r['sigma'], hib)
        delta_pct = round((r['tr']-r['bl'])/r['bl']*100,2) if r['bl'] and abs(r['bl'])>1e-9 else None
        sign = ('≥3σ' if cs and abs(cs)>=3 else '≥2σ' if cs and abs(cs)>=2
                else '≥1σ' if cs and abs(cs)>=1 else '<1σ') if cs is not None else 'N/A'
        tf = tier_fmt(tier); sf = sigma_fmt(cs)
        sm.write(ri,0,name,tf)
        sm.write(ri,1,tier,wb.add_format({'font_name':'Arial','font_size':9,'border':1,'bg_color':TIER_COLORS.get(tier,'#FFF')}))
        sm.write(ri,2,r['bl'],fmt_num)
        sm.write(ri,3,r['tr'],fmt_num)
        sm.write(ri,4,r['pr'] if r['pr'] is not None else 'n/a',fmt_num if r['pr'] is not None else fmt_lbl)
        sm.write(ri,5,delta_pct if delta_pct is not None else 'n/a',fmt_num if delta_pct is not None else fmt_lbl)
        sm.write(ri,6,r['sigma'] if r['sigma'] is not None else 'n/a',fmt_sigma if r['sigma'] is not None else fmt_lbl)
        sm.write(ri,7,cs if cs is not None else 'n/a',sf if cs is not None else fmt_lbl)
        sm.write(ri,8,sign,wb.add_format({'font_name':'Arial','font_size':9,'border':1,'align':'center',
                                           'bg_color':sigma_colour(cs),'font_color':'#FFFFFF' if cs and abs(cs)>=2 else '#000000'}))

    # ── Sheet 3: Sigma Chart ──────────────────────────────────────────────────
    print('  Building Sigma_Chart …')
    sc_ws = wb.add_worksheet('Sigma_Chart')
    sc_ws.hide_gridlines(2)
    sc_ws.set_column('A:A',30); sc_ws.set_column('B:B',12); sc_ws.set_column('C:C',12)
    sc_ws.set_row(0,26)
    sc_ws.write(0,0, f'{rc_label} — {TRIAL_ID} Sigma Significance', fmt_ctitle)
    sc_ws.write(1,0,'KPI',fmt_hdr); sc_ws.write(1,1,'σ (chart)',fmt_hdr); sc_ws.write(1,2,'Tier',fmt_hdr)

    chart_rows = [(NR_COLUMN_MAP[r['col']][0], chart_sigma(r['sigma'],NR_COLUMN_MAP[r['col']][2]),
                   NR_COLUMN_MAP[r['col']][1]) for r in feat_rows_ordered if r['col'] in NR_COLUMN_MAP and r['sigma'] is not None]
    chart_rows = sorted(chart_rows, key=lambda x: (abs(x[1]) if x[1] else 0), reverse=True)

    for ri,(name,cs,tier) in enumerate(chart_rows, start=2):
        sf = sigma_fmt(cs)
        sc_ws.write(ri,0,name,fmt_lbl)
        sc_ws.write(ri,1,cs if cs is not None else 0,sf)
        sc_ws.write(ri,2,tier,fmt_lbl)

    if chart_rows:
        bar = wb.add_chart({'type':'bar'})
        bar.add_series({'name':'Chart sigma (degradation-positive)','categories':['Sigma_Chart',2,0,len(chart_rows)+1,0],
                        'values':['Sigma_Chart',2,1,len(chart_rows)+1,1],
                        'data_labels':{'value':True,'num_format':'+0.00;-0.00;0'},
                        'fill':{'color':'#1F3864'}})
        bar.set_size({'width':900,'height':max(400,len(chart_rows)*20)})
        bar.set_x_axis({'name':'Chart Sigma (degradation-positive → positive)'})
        bar.set_legend({'none':True})
        sc_ws.insert_chart('E2', bar, {'x_offset':5,'y_offset':5})

    # ── Sheet 4: Significance Ranking ────────────────────────────────────────
    print('  Building Significance_Ranking …')
    sr = wb.add_worksheet('Significance_Ranking')
    sr.freeze_panes(1,0)
    sr.set_column('A:A',22); sr.set_column('B:B',10); sr.set_column('C:C',12); sr.set_column('D:D',12); sr.set_column('E:E',10)
    for ci,h in enumerate(['KPI','Tier','σ (raw)','σ (chart)','|σ|']):
        sr.write(0,ci,h,fmt_hdr)
    ranked = sorted([(NR_COLUMN_MAP[r['col']][0], NR_COLUMN_MAP[r['col']][1],
                      r['sigma'], chart_sigma(r['sigma'],NR_COLUMN_MAP[r['col']][2]))
                     for r in feat_stats if r['col'] in NR_COLUMN_MAP and r['sigma'] is not None],
                    key=lambda x: abs(x[3]) if x[3] else 0, reverse=True)
    for ri,(name,tier,raw,cs) in enumerate(ranked, start=1):
        sr.write(ri,0,name,fmt_lbl)
        sr.write(ri,1,tier,fmt_lbl)
        sr.write(ri,2,raw,fmt_sigma)
        sr.write(ri,3,cs,sigma_fmt(cs))
        sr.write(ri,4,abs(cs) if cs else 0,fmt_num)

    # ── Sheet 5: Per_Carrier_Detail ──────────────────────────────────────────
    print('  Building Per_Carrier_Detail …')
    pcd = wb.add_worksheet('Per_Carrier_Detail')
    pcd.freeze_panes(1,1)
    pcd.set_column('A:A',28)
    hdr_pcd = ['KPI']
    for c in carriers:
        hdr_pcd += [f'{c} Baseline', f'{c} Trial', f'{c} σ']
    for ci,h in enumerate(hdr_pcd):
        pcd.write(0,ci,h,fmt_hdr)
        pcd.set_column(ci,ci,14)

    for ri,kpi_col in enumerate(PER_CARRIER_KPIS, start=1):
        if kpi_col not in NR_COLUMN_MAP: continue
        disp = NR_COLUMN_MAP[kpi_col][0]; tier = NR_COLUMN_MAP[kpi_col][1]; hib = NR_COLUMN_MAP[kpi_col][2]
        pcd.write(ri,0,disp,tier_fmt(tier))
        ci = 1
        for carrier in carriers:
            r = pc_data.get(carrier,{}).get(kpi_col)
            if r:
                cs = chart_sigma(r['sigma'],hib)
                pcd.write(ri,ci,r['bl'],fmt_num)
                pcd.write(ri,ci+1,r['tr'],fmt_num)
                pcd.write(ri,ci+2,cs if cs is not None else 'n/a', sigma_fmt(cs) if cs is not None else fmt_lbl)
            else:
                pcd.write(ri,ci,'n/a',fmt_lbl); pcd.write(ri,ci+1,'n/a',fmt_lbl); pcd.write(ri,ci+2,'n/a',fmt_lbl)
            ci += 3

    # ── Sheet 6: Energy_Saving ───────────────────────────────────────────────
    print('  Building Energy_Saving …')
    es_ws = wb.add_worksheet('Energy_Saving')
    es_ws.freeze_panes(1,0); es_ws.hide_gridlines(2)
    es_ws.set_column('A:A',25)
    es_ws.set_row(0,26)
    es_ws.write(0,0,f'{rc_label} — Energy Saving KPIs (per-RC ES report)', fmt_ctitle)
    for ci,h in enumerate(['KPI','Tier','Baseline','Trial','Post-RB','Δ%','σ (raw)','σ (chart)']):
        es_ws.write(1,ci,h,fmt_hdr); es_ws.set_column(ci,ci,14 if ci==0 else 12)

    for ri,r in enumerate(es_stats, start=2):
        col = r['col']
        if col not in NR_ES_COLUMN_MAP: continue
        name,tier,hib = NR_ES_COLUMN_MAP[col]
        cs = chart_sigma(r['sigma'],hib)
        delta_pct = round((r['tr']-r['bl'])/r['bl']*100,2) if r['bl'] and abs(r['bl'])>1e-9 else None
        tf = tier_fmt(tier)
        es_ws.write(ri,0,name,tf)
        es_ws.write(ri,1,tier,fmt_lbl)
        es_ws.write(ri,2,r['bl'],fmt_num)
        es_ws.write(ri,3,r['tr'],fmt_num)
        es_ws.write(ri,4,r['pr'] if r['pr'] is not None else 'n/a', fmt_num if r['pr'] is not None else fmt_lbl)
        es_ws.write(ri,5,delta_pct if delta_pct is not None else 'n/a', fmt_num if delta_pct is not None else fmt_lbl)
        es_ws.write(ri,6,r['sigma'] if r['sigma'] is not None else 'n/a', fmt_sigma if r['sigma'] is not None else fmt_lbl)
        es_ws.write(ri,7,cs if cs is not None else 'n/a', sigma_fmt(cs) if cs is not None else fmt_lbl)

    # ES trajectory charts (daily time-series)
    row_a = len(es_stats) + 4
    es_ws.set_row(row_a, 14)
    es_ws.write(row_a, 0, 'Energy KPI Daily Trajectories (per-RC)', fmt_clbl)
    row_a += 1

    # Build D_ES_Data hidden tab for charts
    des = wb.add_worksheet('D_ES_Data')
    des.freeze_panes(1,1); des.set_column(0,0,13); des.set_row(0,32)
    es_kpi_cols = [c for c in NR_ES_COLUMN_MAP if c in es_df.columns]
    des_hdr = ['Date'] + [NR_ES_COLUMN_MAP[c][0] for c in es_kpi_cols] + ['Trial_Start','Rollback']
    for ci,h in enumerate(des_hdr): des.write(0,ci,h,fmt_hdr); des.set_column(ci,ci,18)
    es_dates_sorted = sorted(es_df['DATETIME'].unique())
    ne = len(es_dates_sorted)
    des_trial_col = len(es_kpi_cols)+1; des_rb_col = len(es_kpi_cols)+2
    fmt_date_d = wb.add_format({'num_format':'DD-MMM-YYYY','font_name':'Arial','font_size':9})
    fmt_num_d  = wb.add_format({'font_name':'Arial','font_size':9,'num_format':'#,##0.00'})
    for ri,dt in enumerate(es_dates_sorted, start=1):
        des.write_datetime(ri,0,dt.to_pydatetime(),fmt_date_d)
        mask = es_df['DATETIME']==dt
        for ci,c in enumerate(es_kpi_cols, start=1):
            sub = es_df.loc[mask,c]
            val = float(sub.iloc[0]) if len(sub)>0 and not sub.isna().all() else None
            if val is not None: des.write_number(ri,ci,val,fmt_num_d)
            else: des.write_blank(ri,ci,None,fmt_num_d)
        des.write_number(ri,des_trial_col,1.0 if dt==TRIAL_START else 0.0,fmt_num_d)
        des.write_number(ri,des_rb_col,   1.0 if (TRIAL_ROLLBACK is not None and dt==TRIAL_ROLLBACK) else 0.0,fmt_num_d)
    des.hide()

    for ci,c in enumerate(es_kpi_cols):
        name_es = NR_ES_COLUMN_MAP[c][0]
        es_ws.set_row(row_a,14); es_ws.write(row_a,0,f'  {name_es}',fmt_clbl); row_a+=1
        lc = wb.add_chart({'type':'line'})
        lc.set_size({'width':780,'height':360})
        lc.set_legend({'position':'right'})
        lc.set_x_axis({'date_axis':True,'num_format':'dd-mmm','major_unit':7,'major_unit_type':'days'})
        lc.set_y_axis({'name':name_es,'num_format':'#,##0'})
        lc.set_y2_axis({'min':0,'max':1,'num_format':';;;','major_gridlines':{'visible':False}})
        lc.add_series({'name':name_es,'categories':['D_ES_Data',1,0,ne,0],'values':['D_ES_Data',1,ci+1,ne,ci+1],
                       'line':{'color':'#8B4513','width':2.0},'marker':{'type':'none'}})
        bc_m = wb.add_chart({'type':'column'})
        bc_m.add_series({'name':'Trial','categories':['D_ES_Data',1,0,ne,0],'values':['D_ES_Data',1,des_trial_col,ne,des_trial_col],
                         'fill':{'color':'#CC0000','transparency':20},'border':{'none':True},'y2_axis':True})
        if TRIAL_ROLLBACK is not None:
            bc_m.add_series({'name':'RB','categories':['D_ES_Data',1,0,ne,0],'values':['D_ES_Data',1,des_rb_col,ne,des_rb_col],
                             'fill':{'color':'#00AA00','transparency':20},'border':{'none':True},'y2_axis':True})
        lc.combine(bc_m)
        es_ws.insert_chart(row_a,0,lc,{'x_offset':5,'y_offset':5}); row_a+=22

    # ── Sheet 7: KPI_Trajectories ─────────────────────────────────────────────
    if feat_ctx:
        print('  Building KPI_Trajectories …')
        kt = wb.add_worksheet('KPI_Trajectories')
        kt.hide_gridlines(2); kt.set_column('A:A',4)
        kt.set_row(0,26); kt.set_row(1,14)
        kt.write(0,0,f'{rc_label} — {TRIAL_ID} Feature Causal-Chain KPI Trajectories', fmt_ctitle)
        kt.write(1,0,'Carrier-stratified daily time-series. Red bar = Trial start; Green bar = Rollback (if applicable). '
                      'Categories: mechanism, outcome, quality, watchdog, context.', fmt_sub)

        # D_KT_Data hidden tab
        dkt = wb.add_worksheet('D_KT_Data')
        dkt.freeze_panes(1,1); dkt.set_column(0,0,13); dkt.set_row(0,32)
        t1_avail = [(col,lbl,unit,cat) for col,lbl,unit,cat in feat_ctx['t1']
                    if col in df.columns and not df[col].isna().all()]
        main_dates = sorted(df['DATETIME'].unique())
        nd = len(main_dates)
        dkt_hdr = ['Date']
        dkt_col_map = {}; cursor = 1
        for col,lbl,unit,cat in t1_avail:
            for carrier in carriers:
                dkt_hdr.append(f'{lbl}_{carrier}')
                dkt_col_map[(col,carrier)] = cursor; cursor+=1
        dkt_trial_col = cursor; dkt_hdr.append('Trial_Start'); cursor+=1
        dkt_rb_col    = cursor; dkt_hdr.append('Rollback');    cursor+=1
        for ci,h in enumerate(dkt_hdr): dkt.write(0,ci,h,fmt_hdr); dkt.set_column(ci,ci,13)
        fmt_date_k = wb.add_format({'num_format':'DD-MMM-YYYY','font_name':'Arial','font_size':9})
        fmt_num_k  = wb.add_format({'font_name':'Arial','font_size':9,'num_format':'#,##0.00'})
        for ri,dt in enumerate(main_dates, start=1):
            dkt.write_datetime(ri,0,dt.to_pydatetime(),fmt_date_k)
            for col,lbl,unit,cat in t1_avail:
                for carrier in carriers:
                    mask = (df['DATETIME']==dt)&(df['CARRIER']==carrier)
                    sub = df.loc[mask,col]
                    val = float(sub.iloc[0]) if len(sub)>0 and not sub.isna().all() else None
                    c_i = dkt_col_map[(col,carrier)]
                    if val is not None: dkt.write_number(ri,c_i,val,fmt_num_k)
                    else: dkt.write_blank(ri,c_i,None,fmt_num_k)
            dkt.write_number(ri,dkt_trial_col,1.0 if dt==TRIAL_START else 0.0,fmt_num_k)
            dkt.write_number(ri,dkt_rb_col,   1.0 if (TRIAL_ROLLBACK is not None and dt==TRIAL_ROLLBACK) else 0.0,fmt_num_k)
        dkt.hide()

        CAT_COLORS = {'mechanism':'#1F77B4','outcome':'#2CA02C','quality':'#9467BD','watchdog':'#D62728','context':'#7F7F7F','traffic_context':'#7F7F7F'}
        row_a = 2
        for col,lbl,unit,cat in t1_avail:
            kt.set_row(row_a,16); kt.write(row_a,0,f'  {lbl} {unit} [{cat}]',fmt_clbl); row_a+=1
            lc = wb.add_chart({'type':'line'})
            lc.set_size({'width':780,'height':360})
            lc.set_legend({'position':'right'})
            lc.set_x_axis({'date_axis':True,'num_format':'dd-mmm','major_unit':7,'major_unit_type':'days'})
            lc.set_y_axis({'name':f'{lbl} {unit}','num_format':'#,##0.00'})
            lc.set_y2_axis({'min':0,'max':1,'num_format':';;;','major_gridlines':{'visible':False}})
            for carrier in carriers:
                c_i = dkt_col_map.get((col,carrier))
                if c_i is None: continue
                lc.add_series({'name':carrier,'categories':['D_KT_Data',1,0,nd,0],
                               'values':['D_KT_Data',1,c_i,nd,c_i],
                               'line':{'color':CARRIER_COLORS.get(carrier,'#888888'),'width':1.5},
                               'marker':{'type':'none'}})
            bc_m = wb.add_chart({'type':'column'})
            bc_m.add_series({'name':'Trial','categories':['D_KT_Data',1,0,nd,0],
                             'values':['D_KT_Data',1,dkt_trial_col,nd,dkt_trial_col],
                             'fill':{'color':'#CC0000','transparency':20},'border':{'none':True},'y2_axis':True})
            if TRIAL_ROLLBACK is not None:
                bc_m.add_series({'name':'RB','categories':['D_KT_Data',1,0,nd,0],
                                 'values':['D_KT_Data',1,dkt_rb_col,nd,dkt_rb_col],
                                 'fill':{'color':'#00AA00','transparency':20},'border':{'none':True},'y2_axis':True})
            lc.combine(bc_m)
            kt.insert_chart(row_a,0,lc,{'x_offset':5,'y_offset':5}); row_a+=22

    wb.close()
    print(f'\n[saved] {out_path}')
    return feat_stats, es_stats, pc_data, carriers


# =============================================================================
# ENTRY POINT
# =============================================================================
if __name__ == '__main__':
    feat_ctx = load_feature_context()
    for rc in RCS:
        print(f'\n{"="*60}\nNR Statistical Analysis — {TRIAL_ID} {rc}\n{"="*60}')
        df = load_main_rc(rc)
        es_df = load_es_rc(rc)
        carriers = [c for c in CARRIER_ORDER if c in df['CARRIER'].values]
        print(f'  RC={rc}, Carriers: {carriers}')
        out_path = f'{OUT_DIR}{TRIAL_ID}_{rc}_NR_Statistical_Analysis.xlsx'
        build_workbook(rc, df, es_df, carriers, feat_ctx, out_path)
        print(f'✓ {rc} done.')
    print('All RCs complete.')
