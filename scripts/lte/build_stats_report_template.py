# =============================================================================
# STATISTICAL ANALYSIS EXCEL GENERATOR — ran-trial-production skill template
# =============================================================================
# REFERENCE TRIAL: CBXXXXXX (<featureParameter>, MNO 4G, RC3/RC4)
#
# TO ADAPT FOR A NEW TRIAL:
#   1. Change OUT path (line below) — replace CBXXXXXX with your TRIAL_ID
#   2. Replace RC3_FEAT and RC4_FEAT arrays (lines ~30-75)
#      Format: (name, tier, higher_bad, BL, Trial, PostRB, sigma)
#      Tier values: 'T1-PS' (power saving), 'T1-Lat' (latency), 'T2' (secondary), 'T3' (watchdog)
#      higher_bad: True if a larger value = degradation (e.g. BLER, fail rate)
#      sigma: float or None (None = baseline variance was ~0, sigma not meaningful)
#   3. Replace BAND_CMP dict (lines ~77-90) — feature vs unaffected for 5 watchdog KPIs
#      Format: (baseline, trial, sigma) — NO kname in the tuple (kname comes from BAND_CMP_KPIS)
#   4. Replace PC_RC3 / PC_RC4 dicts (lines ~92-105) — per-carrier Baseline/Trial pairs
#   5. Update RC_LABELS at line ~200 if RC names differ
#
# DO NOT CHANGE: colour palette, format helpers, chart generation logic, sheet structure
# =============================================================================
import xlsxwriter, os, math, json

OUT = './CBXXXXXX_Statistical_Analysis.xlsx'  # ← EDIT: set your TRIAL_ID  # <-- UPDATE TRIAL_ID HERE

# ─── Colour palette ──────────────────────────────────────────────────────────
DARK_BLUE  = '#1F3864'
MID_BLUE   = '#2F5496'
LIGHT_BLUE = '#D5E8F0'
RED3       = '#C00000'   # |σ| ≥ 3
ORANGE2    = '#E26B0A'   # |σ| ≥ 2
AMBER1     = '#FFC000'   # |σ| ≥ 1
GRAY0      = '#D9D9D9'   # |σ| < 1
PASS_GRN   = '#E2EFDA'
FAIL_RED   = '#FFDDD5'
WARN_YEL   = '#FFF2CC'
WHITE      = '#FFFFFF'
LGRAY      = '#F2F2F2'

# ─── Data ────────────────────────────────────────────────────────────────────
# (name, tier, higher_bad, BL, Trial, PostRB, sigma)
# sigma = None → not calculable (e.g. std dev = 0)
# For significance: sigma sign is already normalised
# (positive sigma = degradation regardless of direction)
def σ_sign(sigma, higher_bad):
    """Return +1 if degradation, -1 if improvement, 0 if neutral/None."""
    if sigma is None: return 0
    if higher_bad:  return +1 if sigma > 0 else -1
    else:           return +1 if sigma < 0 else -1

RC3_FEAT = [
    ('PSM Ratio',           'T1-PS',  False, 15.20, 15.49, 15.81,  0.5),
    ('ReducedTX Ratio',     'T1-PS',  False,  8.12,  8.30,  8.40,  0.6),
    ('DRX Sleep Ratio',     'T1-PS',  False, 63.85, 63.80, 64.38, -0.2),
    ('Avg Latency DL',      'T1-Lat', True,  86.3,  84.7,  85.7,  -1.0),
    ('SDU Delay QCI1',      'T1-Lat', True,  11.00, 10.97, 11.00, -0.2),
    ('SDU Delay QCI8',      'T1-Lat', True, 118.0, 115.9, 117.0,  -0.6),
    ('SDU Delay QCI9',      'T1-Lat', True,  32.46, 33.14, 33.65,  0.3),
    ('UL rBLER',            'T2',     True,   0.949, 0.993, 1.017,  2.3),
    ('DL rBLER',            'T2',     True,   0.022, 0.022, 0.022,  0.3),
    ('Avg UL MCS',          'T2',     False, 10.25, 10.10, 10.00,  None),
    ('DL Spectral Eff',     'T2',     False,  1.700, 1.686, 1.676, -0.5),
    ('Tput DL Active',      'T2',     False, 10671, 10503, 10462,  -0.4),
    ('Tput UL Active',      'T2',     False,  1838,  1801,  1823,  -0.4),
    ('Cell Availability',   'T3',     False, 84.16, 83.93, 83.44, -0.3),
    ('RACH SR',             'T3',     False, 97.69, 97.89, 97.82,  0.9),
    ('E-RAB SR',            'T3',     False, 99.788,99.783,99.799,-0.3),
    ('RRC SR',              'T3',     False, 99.756,99.729,99.739, -1.2),
    ('E-RAB Drop Ratio',    'T3',     True,   0.434, 0.494, 0.527,  1.4),
    ('ERAB Retain. Fail',   'T3',     True,   1.239, 1.553, 2.329,  3.7),
    ('HO Intra-eNB SR',     'T3',     False, 99.176,99.116,99.119,-0.9),
]

RC4_FEAT = [
    ('PSM Ratio',           'T1-PS',  False, 14.21, 14.29, 13.99,  0.1),
    ('ReducedTX Ratio',     'T1-PS',  False,  6.86,  7.03,  7.02,  0.5),
    ('DRX Sleep Ratio',     'T1-PS',  False, 65.43, 65.71, 66.32,  1.8),
    ('Avg Latency DL',      'T1-Lat', True, 123.9, 121.7, 124.3,  -0.9),
    ('SDU Delay QCI1',      'T1-Lat', True,  11.18, 11.21, 11.25,  0.2),
    ('SDU Delay QCI8',      'T1-Lat', True, 157.0, 153.9, 156.4,  -0.6),
    ('SDU Delay QCI9',      'T1-Lat', True,  36.18, 36.86, 37.62,  0.4),
    ('UL rBLER',            'T2',     True,   1.274, 1.297, 1.318,  0.7),
    ('DL rBLER',            'T2',     True,   0.026, 0.025, 0.025, -0.1),
    ('Avg UL MCS',          'T2',     False,  9.21,  9.07,  8.98, -1.5),
    ('DL Spectral Eff',     'T2',     False,  1.399, 1.406, 1.408,  0.2),
    ('Tput DL Active',      'T2',     False,  9628,  9669,  9711,  0.1),
    ('Tput UL Active',      'T2',     False,  1376,  1383,  1414,  0.2),
    ('Cell Availability',   'T3',     False, 85.14, 85.11, 85.45,  0.0),
    ('RACH SR',             'T3',     False, 98.717,98.642,98.565,-0.5),
    ('E-RAB SR',            'T3',     False, 99.756,99.754,99.722,-0.1),
    ('RRC SR',              'T3',     False, 99.729,99.660,99.637,-3.8),
    ('E-RAB Drop Ratio',    'T3',     True,   0.435, 0.438, 0.513,  0.1),
    ('ERAB Retain. Fail',   'T3',     True,   2.178, 2.278, 2.516,  0.2),
    ('HO Intra-eNB SR',     'T3',     False, 97.151,96.366,96.271,-3.2),
]

# Band comparison: feature vs unaffected for key watchdog KPIs
BAND_CMP_KPIS = [
    'ERAB Retain. Fail', 'UL rBLER', 'E-RAB Drop Ratio', 'Cell Availability', 'PSM Ratio'
]
BAND_CMP = {
    'RC3': {
        'feat':  [(1.239,1.553, 3.7),(0.949,0.993, 2.3),(0.434,0.494, 1.4),(84.16,83.93,-0.3),(15.20,15.49, 0.5)],
        'unaff': [(1.946,2.652, 3.2),(0.693,0.730, 1.9),(0.173,0.186, 0.7),(87.99,86.88,-3.8),(11.85,10.98,-2.0)],
    },
    'RC4': {
        'feat':  [(2.178,2.278, 0.2),(1.274,1.297, 0.7),(0.435,0.438, 0.1),(85.14,85.11, 0.0),(14.21,14.29, 0.1)],
        'unaff': [(3.709,4.895, 3.2),(0.856,1.097, 6.1),(0.197,0.270, 1.9),(87.65,87.57,-0.2),(9.98,10.07, 0.3)],
    },
}

# Per-carrier: (BL, Trial)
PC_RC3 = {
    'DRX Sleep':   {'B800':(66.13,66.02),'B900':(65.22,65.04),'B1800':(51.01,51.16),'B2100':(73.05,72.98)},
    'Latency DL':  {'B800':(122.4,120.6),'B900':(95.1,93.9),'B1800':(57.6,55.7),'B2100':(69.9,68.4)},
    'QCI8 Delay':  {'B800':(162.1,159.9),'B900':(132.6,130.5),'B1800':(84.7,82.6),'B2100':(92.4,90.6)},
    'PSM Ratio':   {'B900':(27.4,27.5),'B1800':(33.4,34.5)},
    'ReducedTX':   {'B2100':(32.5,33.2)},
}
PC_RC4 = {
    'DRX Sleep':   {'B800':(68.61,68.58),'B900':(66.73,66.92),'B1800':(52.75,53.74),'B2100':(73.61,73.61)},
    'Latency DL':  {'B800':(177.6,173.4),'B900':(143.0,140.7),'B1800':(81.3,80.1),'B2100':(93.9,92.4)},
    'QCI8 Delay':  {'B800':(220.9,215.4),'B900':(179.0,175.6),'B1800':(111.0,109.3),'B2100':(117.1,115.2)},
    'PSM Ratio':   {'B900':(24.5,24.0),'B1800':(32.4,33.2)},
    'ReducedTX':   {'B2100':(27.5,28.1)},
}

# ─── Feature context (dynamic KPI_Trajectories KPIs) ──────────────────────
def load_feature_context(search_dir=None):
    """Load feature_context.json from the script directory.

    LTE format — each entry in t1_kpis:
        {"col": "<name matching RC3/RC4_FEAT>", "unit": "(%)",
         "higher_bad": true/false, "category": "mechanism|outcome|watchdog|context"}

    The 'col' value MUST match the name field in RC3_FEAT / RC4_FEAT rows.
    No t1_es_kpis for LTE (energy KPIs come from the same extract, not a separate ES file).

    Returns dict with keys 't1', 'doc', 'name', 'mechanism', or None if file absent.
    When None, KPI_Trajectories falls back to the default hardcoded TRAJ_KPIS list.
    """
    if search_dir is None:
        search_dir = os.path.dirname(os.path.abspath(__file__))
    fpath = os.path.join(search_dir, 'feature_context.json')
    if not os.path.exists(fpath):
        print(f'[warn] feature_context.json not found at {fpath}')
        print('       KPI_Trajectories will use default TRAJ_KPIS.')
        return None
    with open(fpath, encoding='utf-8') as fh:
        ctx = json.load(fh)
    t1 = [(k['col'], k['unit'], k['higher_bad']) for k in ctx.get('t1_kpis', [])]
    doc  = ctx.get('feature_doc', '')
    name = ctx.get('feature_name', '')
    mech = ctx.get('mechanism_summary', '')
    print(f'load_feature_context: loaded {len(t1)} trajectory KPIs from feature_context.json')
    print(f'  Feature: {name} ({doc})')
    return {'t1': t1, 'doc': doc, 'name': name, 'mechanism': mech}

_FEATURE_CTX = load_feature_context()

# ─── Workbook ────────────────────────────────────────────────────────────────
wb = xlsxwriter.Workbook(OUT)

# ─── Formats ─────────────────────────────────────────────────────────────────
def fmt(**kw):
    base = {'font_name':'Arial','font_size':10,'border':1,'border_color':'#AAAAAA'}
    base.update(kw)
    return wb.add_format(base)

hdr      = fmt(bold=True,bg_color=DARK_BLUE,font_color='#FFFFFF',font_size=10,align='center',valign='vcenter')
hdr_mid  = fmt(bold=True,bg_color=MID_BLUE, font_color='#FFFFFF',font_size=10,align='center',valign='vcenter')
hdr_lb   = fmt(bold=True,bg_color=LIGHT_BLUE,font_color='#000000',font_size=10,align='center',valign='vcenter')
title_f  = fmt(bold=True,font_size=14,font_color=DARK_BLUE,border=0)
sub_f    = fmt(bold=True,font_size=11,font_color=MID_BLUE,border=0)
kpi_f    = fmt(align='left',valign='vcenter')
num_f    = fmt(num_format='0.000',align='center',valign='vcenter')
pct_f    = fmt(num_format='0.0%',align='center',valign='vcenter')
pct2_f   = fmt(num_format='+0.0%;-0.0%;0.0%',align='center',valign='vcenter')
sig_f    = fmt(num_format='0.0',align='center',valign='vcenter')
ctr_f    = fmt(align='center',valign='vcenter')
tier_f   = fmt(align='center',valign='vcenter',bold=True,font_color=MID_BLUE)
note_f   = fmt(italic=True,font_size=9,border=0,font_color='#666666')

# sigma-level cell formats
def sigma_fmt(sigma, higher_bad):
    if sigma is None:
        return fmt(num_format='"-"',align='center',valign='vcenter',bg_color=LGRAY)
    deg = σ_sign(sigma, higher_bad)
    absσ = abs(sigma)
    if deg > 0:  # degradation
        if absσ >= 3:   bg = RED3;    fc = '#FFFFFF'
        elif absσ >= 2: bg = ORANGE2; fc = '#FFFFFF'
        elif absσ >= 1: bg = AMBER1;  fc = '#000000'
        else:           bg = LGRAY;   fc = '#000000'
    elif deg < 0:  # improvement
        if absσ >= 2:   bg = '#375623'; fc = '#FFFFFF'
        elif absσ >= 1: bg = PASS_GRN;  fc = '#000000'
        else:           bg = LGRAY;     fc = '#000000'
    else:
        bg = LGRAY; fc = '#000000'
    return fmt(num_format='0.0σ',align='center',valign='vcenter',bg_color=bg,font_color=fc,bold=(absσ>=2))

def delta_fmt(bl, trial, higher_bad):
    if bl == 0: return fmt(num_format='"-"',align='center',valign='vcenter')
    dp = (trial - bl) / abs(bl)
    deg = (dp > 0 and higher_bad) or (dp < 0 and not higher_bad)
    absv = abs(dp)
    if absv < 0.005:
        bg = LGRAY
    elif deg:
        bg = FAIL_RED if absv >= 0.03 else WARN_YEL
    else:
        bg = PASS_GRN if absv >= 0.01 else LGRAY
    return fmt(num_format='+0.0%;-0.0%;0.0%',align='center',valign='vcenter',bg_color=bg,bold=absv>=0.03)


# ════════════════════════════════════════════════════════════════════════════
# SHEET 1: Dashboard — Significance Matrix
# ════════════════════════════════════════════════════════════════════════════
ws = wb.add_worksheet('Significance_Matrix')
ws.set_tab_color(DARK_BLUE)
ws.set_zoom(85)

ws.set_column('A:A', 22)
ws.set_column('B:B', 8)
ws.set_column('C:C', 9)  # Baseline
ws.set_column('D:D', 9)  # Trial
ws.set_column('E:E', 9)  # Post-RB
ws.set_column('F:F', 9)  # Δ%
ws.set_column('G:G', 8)  # σ
ws.set_column('H:H', 8)  # Significance
ws.set_column('I:I', 2)  # gap
ws.set_column('J:J', 22) # KPI (RC4)
ws.set_column('K:K', 8)
ws.set_column('L:L', 9)
ws.set_column('M:M', 9)
ws.set_column('N:N', 9)
ws.set_column('O:O', 9)
ws.set_column('P:P', 8)
ws.set_column('Q:Q', 8)

# Title
ws.merge_range('A1:Q1', 'CBXXXXXX — Trial Statistical Analysis: Feature Bands (B800 / B900 / B1800 / B2100)', title_f)
ws.set_row(0, 22)
ws.merge_range('A2:Q2', '<featureParameter> = 0  |  Baseline: 28-Jan – 03-Feb  |  Trial: 04-Feb – 02-Mar  |  Post-RB: 03–15-Mar',
               fmt(italic=True, font_size=10, border=0, font_color='#444444'))
ws.set_row(1, 16)

# Legend row
ws.set_row(3, 14)
ws.write('A4', 'Significance key:', fmt(bold=True,border=0,font_size=9))
for col, (label, bg, fc) in enumerate([
    ('|σ| ≥ 3  CRITICAL', RED3, '#FFFFFF'),
    ('|σ| ≥ 2  HIGH',     ORANGE2, '#FFFFFF'),
    ('|σ| ≥ 1  MEDIUM',   AMBER1, '#000000'),
    ('|σ| < 1  NOISE',    LGRAY, '#000000'),
    ('≥ 1σ improve.',     PASS_GRN, '#000000'),
], start=1):
    ws.write(3, col+1, label, fmt(bold=True,bg_color=bg,font_color=fc,align='center',font_size=9,border=1))

# Column headers — RC3
row = 5
ws.set_row(row, 28)
for col, txt in enumerate(['KPI (RC3 Feature Bands)', 'Tier', 'Baseline', 'Trial', 'Post-RB', 'Δ%', 'σ', 'Signif.']):
    ws.write(row, col, txt, hdr)
ws.write(row, 8, '', fmt(border=0))  # gap
for col, txt in enumerate(['KPI (RC4 Feature Bands)', 'Tier', 'Baseline', 'Trial', 'Post-RB', 'Δ%', 'σ', 'Signif.']):
    ws.write(row, col+9, txt, hdr)

TIER_COLORS = {
    'T1-PS':  '#EBF3FB', 'T1-Lat': '#FFF9F0',
    'T2':     '#F5F5F5', 'T3':     '#FFF0F0',
}
SIGNIF_LABELS = {None: '—', 0: 'Noise'}
def signif_label(sigma, higher_bad):
    if sigma is None: return '—'
    absσ = abs(sigma)
    deg = σ_sign(sigma, higher_bad)
    if absσ >= 3: return '★★★ CRITICAL' if deg>0 else '▲▲▲ Strong'
    if absσ >= 2: return '★★ HIGH'      if deg>0 else '▲▲ Strong'
    if absσ >= 1: return '★ MEDIUM'     if deg>0 else '▲ Improve'
    return 'Noise'

def signif_bg(sigma, higher_bad):
    if sigma is None: return LGRAY
    deg = σ_sign(sigma, higher_bad)
    absσ = abs(sigma)
    if deg > 0:
        if absσ >= 3: return RED3
        if absσ >= 2: return ORANGE2
        if absσ >= 1: return AMBER1
        return LGRAY
    elif deg < 0:
        if absσ >= 2: return '#375623'
        if absσ >= 1: return PASS_GRN
    return LGRAY

for i, (r3, r4) in enumerate(zip(RC3_FEAT, RC4_FEAT)):
    r = row + 1 + i
    ws.set_row(r, 16)
    bg = TIER_COLORS.get(r3[1], WHITE)

    # RC3
    name3, tier3, hb3, bl3, tr3, pr3, sg3 = r3
    dp3 = (tr3-bl3)/abs(bl3) if bl3 else 0
    ws.write(r, 0, name3, fmt(align='left',valign='vcenter',bg_color=bg))
    ws.write(r, 1, tier3, fmt(align='center',valign='vcenter',bg_color=bg,bold=True,font_color=MID_BLUE))
    ws.write(r, 2, bl3,  fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 3, tr3,  fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 4, pr3,  fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 5, dp3,  delta_fmt(bl3,tr3,hb3))
    ws.write(r, 6, sg3 if sg3 is not None else None,
             fmt(num_format='0.0σ' if sg3 is not None else '"-"',
                 align='center',valign='vcenter',
                 bg_color=signif_bg(sg3,hb3), bold=bool(sg3 and abs(sg3)>=2),
                 font_color='#FFFFFF' if sg3 and abs(sg3)>=2 and σ_sign(sg3,hb3)>0 else '#000000'))
    sl = signif_label(sg3, hb3)
    sl_bg = signif_bg(sg3, hb3)
    ws.write(r, 7, sl, fmt(align='center',valign='vcenter',bg_color=sl_bg,
                            bold=bool(sg3 and abs(sg3)>=2),
                            font_color='#FFFFFF' if sg3 and abs(sg3)>=2 and σ_sign(sg3,hb3)>0 else '#000000',
                            font_size=9))
    ws.write(r, 8, '', fmt(border=0))  # gap

    # RC4
    name4, tier4, hb4, bl4, tr4, pr4, sg4 = r4
    dp4 = (tr4-bl4)/abs(bl4) if bl4 else 0
    ws.write(r, 9,  name4, fmt(align='left',valign='vcenter',bg_color=bg))
    ws.write(r, 10, tier4, fmt(align='center',valign='vcenter',bg_color=bg,bold=True,font_color=MID_BLUE))
    ws.write(r, 11, bl4, fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 12, tr4, fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 13, pr4, fmt(num_format='0.000',align='center',valign='vcenter',bg_color=bg))
    ws.write(r, 14, dp4, delta_fmt(bl4,tr4,hb4))
    ws.write(r, 15, sg4 if sg4 is not None else None,
             fmt(num_format='0.0σ' if sg4 is not None else '"-"',
                 align='center',valign='vcenter',
                 bg_color=signif_bg(sg4,hb4), bold=bool(sg4 and abs(sg4)>=2),
                 font_color='#FFFFFF' if sg4 and abs(sg4)>=2 and σ_sign(sg4,hb4)>0 else '#000000'))
    sl4 = signif_label(sg4, hb4)
    sl4_bg = signif_bg(sg4, hb4)
    ws.write(r, 16, sl4, fmt(align='center',valign='vcenter',bg_color=sl4_bg,
                              bold=bool(sg4 and abs(sg4)>=2),
                              font_color='#FFFFFF' if sg4 and abs(sg4)>=2 and σ_sign(sg4,hb4)>0 else '#000000',
                              font_size=9))

last_data_row = row + len(RC3_FEAT)
ws.write(last_data_row+1, 0, '▲ Feature bands: B800/B900/B1800/B2100 (parameter changed). Sigma based on 7-day baseline — treat |σ| < 2 as directional only.', note_f)
ws.write(last_data_row+2, 0, 'For "Higher is Bad" KPIs: positive delta/sigma = degradation. For "Higher is Good" KPIs: negative delta/sigma = degradation.', note_f)


# ════════════════════════════════════════════════════════════════════════════
# SHEET 2: Sigma Charts
# ════════════════════════════════════════════════════════════════════════════
ws2 = wb.add_worksheet('Sigma_Charts')
ws2.set_tab_color(MID_BLUE)
ws2.set_zoom(85)
ws2.set_column('A:A', 22)
ws2.set_column('B:D', 9)
ws2.set_column('E:E', 2)
ws2.set_column('F:H', 9)

ws2.merge_range('A1:H1', 'Sigma Significance — Feature Bands (B800/B900/B1800/B2100)', title_f)
ws2.set_row(0, 22)
ws2.merge_range('A2:H2', 'Positive sigma = degradation on "higher is bad" KPIs. For "higher is good" KPIs, sigma sign is inverted to show degradation as positive.', note_f)

# Helper: convert raw sigma to "degradation-positive" sigma for charting
def calc_deg_sigma(sigma, higher_bad):
    if sigma is None: return 0
    # higher_bad: sigma>0 = degradation → keep sign
    # higher_good: sigma<0 = degradation → invert
    return sigma if higher_bad else -sigma

# Build data table for sigma chart
sigma_data = []
for r3, r4 in zip(RC3_FEAT, RC4_FEAT):
    name3, tier3, hb3, bl3, tr3, pr3, sg3 = r3
    name4, tier4, hb4, bl4, tr4, pr4, sg4 = r4
    sigma_data.append((name3, calc_deg_sigma(sg3,hb3), calc_deg_sigma(sg4,hb4)))

# Write data table starting at row 4
hdr_row = 3
ws2.write(hdr_row, 0, 'KPI', hdr)
ws2.write(hdr_row, 1, 'RC3 σ (deg+)', hdr)
ws2.write(hdr_row, 2, 'RC4 σ (deg+)', hdr)
ws2.write(hdr_row, 3, '|σ|≥2 ref line', hdr)
ws2.write(hdr_row, 4, '', fmt(border=0))
ws2.write(hdr_row, 5, 'KPI', hdr)
ws2.write(hdr_row, 6, 'RC3 Δ%', hdr)
ws2.write(hdr_row, 7, 'RC4 Δ%', hdr)

for i, (r3, r4) in enumerate(zip(RC3_FEAT, RC4_FEAT)):
    r = hdr_row + 1 + i
    ws2.set_row(r, 16)
    name3, tier3, hb3, bl3, tr3, pr3, sg3 = r3
    name4, tier4, hb4, bl4, tr4, pr4, sg4 = r4
    cs3 = calc_deg_sigma(sg3, hb3)
    cs4 = calc_deg_sigma(sg4, hb4)
    dp3 = (tr3-bl3)/abs(bl3) if bl3 else 0
    dp4 = (tr4-bl4)/abs(bl4) if bl4 else 0
    ws2.write(r, 0, name3, kpi_f)
    ws2.write(r, 1, cs3, num_f)
    ws2.write(r, 2, cs4, num_f)
    ws2.write(r, 3, 2.0, num_f)   # reference threshold line
    ws2.write(r, 4, '', fmt(border=0))
    ws2.write(r, 5, name3, kpi_f)
    ws2.write(r, 6, dp3, pct2_f)
    ws2.write(r, 7, dp4, pct2_f)

ndata = len(RC3_FEAT)
dr0 = hdr_row + 1  # first data row (0-indexed)
dr1 = dr0 + ndata - 1  # last data row

# ── Sigma bar chart ──
sigma_chart = wb.add_chart({'type': 'bar'})
sigma_chart.add_series({
    'name': 'RC3 σ (degrad.+)',
    'categories': ['Sigma_Charts', dr0, 0, dr1, 0],
    'values':     ['Sigma_Charts', dr0, 1, dr1, 1],
    'fill': {'color': MID_BLUE},
    'gap': 60,
})
sigma_chart.add_series({
    'name': 'RC4 σ (degrad.+)',
    'categories': ['Sigma_Charts', dr0, 0, dr1, 0],
    'values':     ['Sigma_Charts', dr0, 2, dr1, 2],
    'fill': {'color': '#70AD47'},
})
# Reference line series at 2σ
sigma_chart.add_series({
    'name': '±2σ threshold',
    'categories': ['Sigma_Charts', dr0, 0, dr1, 0],
    'values':     ['Sigma_Charts', dr0, 3, dr1, 3],
    'type': 'line',
    'line': {'color': RED3, 'width': 1.5, 'dash_type': 'dash'},
    'marker': {'type': 'none'},
})
sigma_chart.set_title({'name': 'Sigma Significance — RC3 vs RC4 Feature Bands'})
sigma_chart.set_x_axis({'name': 'Sigma (degradation = positive)',
                         'min': -5, 'max': 5,
                         'crossing': 0,
                         'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                         'line': {'color': '#666666'}})
sigma_chart.set_y_axis({'name': '', 'line': {'none': True}})
sigma_chart.set_legend({'position': 'bottom'})
sigma_chart.set_size({'width': 700, 'height': 520})
sigma_chart.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
ws2.insert_chart('J4', sigma_chart, {'x_offset': 5, 'y_offset': 5})

# ── Delta % bar chart ──
chart_delta = wb.add_chart({'type': 'bar'})
chart_delta.add_series({
    'name': 'RC3 Δ%',
    'categories': ['Sigma_Charts', dr0, 5, dr1, 5],
    'values':     ['Sigma_Charts', dr0, 6, dr1, 6],
    'fill': {'color': MID_BLUE},
    'gap': 60,
})
chart_delta.add_series({
    'name': 'RC4 Δ%',
    'categories': ['Sigma_Charts', dr0, 5, dr1, 5],
    'values':     ['Sigma_Charts', dr0, 7, dr1, 7],
    'fill': {'color': '#ED7D31'},
})
chart_delta.set_title({'name': 'Delta % (Trial vs Baseline) — RC3 vs RC4 Feature Bands'})
chart_delta.set_x_axis({'name': 'Delta %', 'num_format': '0.0%', 'crossing': 0,
                         'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                         'line': {'color': '#666666'}})
chart_delta.set_y_axis({'name': '', 'line': {'none': True}})
chart_delta.set_legend({'position': 'bottom'})
chart_delta.set_size({'width': 700, 'height': 520})
chart_delta.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
ws2.insert_chart('J34', chart_delta, {'x_offset': 5, 'y_offset': 5})


# ════════════════════════════════════════════════════════════════════════════
# SHEET 3: Period Trajectories — key KPIs
# ════════════════════════════════════════════════════════════════════════════
ws3 = wb.add_worksheet('KPI_Trajectories')
ws3.set_tab_color('#ED7D31')
ws3.set_zoom(85)
ws3.set_column('A:A', 18)
ws3.set_column('B:I', 11)

ws3.merge_range('A1:I1', 'KPI Period Trajectories: Baseline → Trial → Post-Rollback', title_f)
ws3.set_row(0, 22)

# Key KPIs for KPI_Trajectories — loaded from feature_context.json if present.
_DEFAULT_TRAJ_KPIS = [
    # Fallback list used when feature_context.json is absent.
    # This matches the CBXXXXXX reference trial (<featureParameter>).
    ('ERAB Retain. Fail', '%', True),
    ('UL rBLER',           '%', True),
    ('SDU Delay QCI8',     'ms', True),
    ('Avg Latency DL',     'ms', True),
    ('PSM Ratio',          '%', False),
    ('DRX Sleep Ratio',    '%', False),
    ('E-RAB Drop Ratio',   '%', True),
    ('HO Intra-eNB SR',    '%', False),
]
if _FEATURE_CTX is not None:
    TRAJ_KPIS = _FEATURE_CTX['t1']
    print(f'  KPI_Trajectories: {len(TRAJ_KPIS)} feature-context KPIs loaded')
else:
    TRAJ_KPIS = _DEFAULT_TRAJ_KPIS
    print('  KPI_Trajectories: using fallback TRAJ_KPIS (no feature_context.json)')

# Extract values for these KPIs
def get_kpi(dataset, name):
    for row in dataset:
        if row[0] == name:
            return row[3], row[4], row[5]  # BL, TR, PR
    return None, None, None

# Build data tables
row_off = 2
periods = ['Baseline', 'Trial', 'Post-RB']

# RC3 table
ws3.merge_range(row_off, 0, row_off, 3, 'RC3 Feature Bands', hdr_mid)
ws3.set_row(row_off, 18)
row_off += 1
ws3.write(row_off, 0, 'KPI', hdr)
for j, p in enumerate(periods):
    ws3.write(row_off, j+1, p, hdr)
ws3.write(row_off, 4, 'Δ% (Trial)', hdr)
row_off += 1

rc3_traj_start = row_off
for kname, unit, hib in TRAJ_KPIS:
    bl, tr, pr = get_kpi(RC3_FEAT, kname)
    if bl is None: continue
    dp = (tr-bl)/abs(bl) if bl else 0
    ws3.write(row_off, 0, f'{kname} ({unit})', kpi_f)
    ws3.write(row_off, 1, bl, num_f)
    ws3.write(row_off, 2, tr, num_f)
    ws3.write(row_off, 3, pr, num_f)
    ws3.write(row_off, 4, dp, delta_fmt(bl, tr, hib))
    row_off += 1
rc3_traj_end = row_off - 1

row_off += 1

# RC4 table
ws3.merge_range(row_off, 0, row_off, 3, 'RC4 Feature Bands', hdr_mid)
ws3.set_row(row_off, 18)
row_off += 1
ws3.write(row_off, 0, 'KPI', hdr)
for j, p in enumerate(periods):
    ws3.write(row_off, j+1, p, hdr)
ws3.write(row_off, 4, 'Δ% (Trial)', hdr)
row_off += 1

rc4_traj_start = row_off
for kname, unit, hib in TRAJ_KPIS:
    bl, tr, pr = get_kpi(RC4_FEAT, kname)
    if bl is None: continue
    dp = (tr-bl)/abs(bl) if bl else 0
    ws3.write(row_off, 0, f'{kname} ({unit})', kpi_f)
    ws3.write(row_off, 1, bl, num_f)
    ws3.write(row_off, 2, tr, num_f)
    ws3.write(row_off, 3, pr, num_f)
    ws3.write(row_off, 4, dp, delta_fmt(bl, tr, hib))
    row_off += 1
rc4_traj_end = row_off - 1

# ── Charts: BL/Trial/PostRB for Retainability and UL rBLER ──
# For each, create a grouped column chart
for rc_label, traj_start, traj_end, dataset in [
    ('RC3', rc3_traj_start, rc3_traj_end, RC3_FEAT),
    ('RC4', rc4_traj_start, rc4_traj_end, RC4_FEAT),
]:
    chart = wb.add_chart({'type': 'column'})
    for per_idx, (period, color) in enumerate(zip(
        ['Baseline', 'Trial', 'Post-RB'],
        [DARK_BLUE, '#ED7D31', '#70AD47']
    )):
        chart.add_series({
            'name': period,
            'categories': ['KPI_Trajectories', traj_start, 0, traj_end, 0],
            'values':     ['KPI_Trajectories', traj_start, per_idx+1, traj_end, per_idx+1],
            'fill': {'color': color},
            'gap': 80,
        })
    chart.set_title({'name': f'{rc_label} Feature Bands — KPI Period Comparison'})
    chart.set_x_axis({'name': '', 'num_font': {'rotation': -45},
                       'major_gridlines': {'visible': False},
                       'line': {'color': '#666666'}})
    chart.set_y_axis({'name': 'KPI Value',
                       'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                       'line': {'color': '#666666'}})
    chart.set_legend({'position': 'bottom'})
    chart.set_size({'width': 620, 'height': 380})
    chart.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
    col_insert = 6 if rc_label == 'RC3' else 6
    row_insert = 2 if rc_label == 'RC3' else 25
    ws3.insert_chart(row_insert, col_insert, chart, {'x_offset': 5, 'y_offset': 5})


# ════════════════════════════════════════════════════════════════════════════
# SHEET 4: Band Comparison — Feature vs Unaffected
# ════════════════════════════════════════════════════════════════════════════
ws4 = wb.add_worksheet('Band_Comparison')
ws4.set_tab_color(RED3)
ws4.set_zoom(85)
ws4.set_column('A:A', 22)
ws4.set_column('B:I', 11)

ws4.merge_range('A1:I1', 'Feature Bands vs Unaffected Bands — Impact Check', title_f)
ws4.set_row(0, 22)
ws4.merge_range('A2:I2',
    'Degradation on unaffected bands (B700/B2300) cannot be attributed to CBXXXXXX — indicates confounding factors.',
    note_f)

def write_bandcmp_table(ws, row_off, rc_label):
    ws.merge_range(row_off, 0, row_off, 7, f'{rc_label} — Feature vs Unaffected Band Comparison', hdr_mid)
    ws.set_row(row_off, 18)
    row_off += 1

    # Headers
    ws.write(row_off, 0, 'KPI', hdr)
    ws.write(row_off, 1, 'Feat. BL', hdr)
    ws.write(row_off, 2, 'Feat. Trial', hdr)
    ws.write(row_off, 3, 'Feat. Δ%', hdr)
    ws.write(row_off, 4, 'Feat. σ', hdr)
    ws.write(row_off, 5, 'Unaff. BL', hdr)
    ws.write(row_off, 6, 'Unaff. Trial', hdr)
    ws.write(row_off, 7, 'Unaff. Δ%', hdr)
    ws.write(row_off, 8, 'Unaff. σ', hdr)
    row_off += 1

    start = row_off
    for kname, (fbl, ftr, fsg), (ubl, utr, usg) in zip(
        BAND_CMP_KPIS, BAND_CMP[rc_label]['feat'], BAND_CMP[rc_label]['unaff']
    ):
        hib = kname in ('ERAB Retain. Fail','UL rBLER','E-RAB Drop Ratio')
        fdp = (ftr-fbl)/abs(fbl) if fbl else 0
        udp = (utr-ubl)/abs(ubl) if ubl else 0
        ws.write(row_off, 0, kname, kpi_f)
        ws.write(row_off, 1, fbl, num_f)
        ws.write(row_off, 2, ftr, num_f)
        ws.write(row_off, 3, fdp, delta_fmt(fbl,ftr,hib))
        ws.write(row_off, 4, fsg,
                 fmt(num_format='0.0σ',align='center',valign='vcenter',
                     bg_color=signif_bg(fsg,hib), bold=abs(fsg)>=2,
                     font_color='#FFFFFF' if abs(fsg)>=2 and σ_sign(fsg,hib)>0 else '#000000'))
        ws.write(row_off, 5, ubl, num_f)
        ws.write(row_off, 6, utr, num_f)
        ws.write(row_off, 7, udp, delta_fmt(ubl,utr,hib))
        ws.write(row_off, 8, usg,
                 fmt(num_format='0.0σ',align='center',valign='vcenter',
                     bg_color=signif_bg(usg,hib), bold=abs(usg)>=2,
                     font_color='#FFFFFF' if abs(usg)>=2 and σ_sign(usg,hib)>0 else '#000000'))
        row_off += 1
    return row_off, start

row4 = 3
row4, rc3_bc_start = write_bandcmp_table(ws4, row4, 'RC3')
row4 += 1
row4, rc4_bc_start = write_bandcmp_table(ws4, row4, 'RC4')

# Band comparison chart — Delta% for feature vs unaffected (RC3 and RC4)
# Build a data table: KPI | RC3 Feat Δ% | RC3 Unaff Δ% | RC4 Feat Δ% | RC4 Unaff Δ%
bc_row = row4 + 2
ws4.write(bc_row, 0, 'KPI', hdr)
ws4.write(bc_row, 1, 'RC3 Feat Δ%', hdr)
ws4.write(bc_row, 2, 'RC3 Unaff Δ%', hdr)
ws4.write(bc_row, 3, 'RC4 Feat Δ%', hdr)
ws4.write(bc_row, 4, 'RC4 Unaff Δ%', hdr)
bc_data_start = bc_row + 1

for i, (kname, (fbl3, ftr3, fsg3), (ubl3, utr3, usg3), (fbl4, ftr4, fsg4), (ubl4, utr4, usg4)) in enumerate(zip(
    BAND_CMP_KPIS,
    BAND_CMP['RC3']['feat'], BAND_CMP['RC3']['unaff'],
    BAND_CMP['RC4']['feat'], BAND_CMP['RC4']['unaff'],
)):
    r = bc_data_start + i
    ws4.write(r, 0, kname, kpi_f)
    ws4.write(r, 1, (ftr3-fbl3)/abs(fbl3) if fbl3 else 0, pct2_f)
    ws4.write(r, 2, (utr3-ubl3)/abs(ubl3) if ubl3 else 0, pct2_f)
    ws4.write(r, 3, (ftr4-fbl4)/abs(fbl4) if fbl4 else 0, pct2_f)
    ws4.write(r, 4, (utr4-ubl4)/abs(ubl4) if ubl4 else 0, pct2_f)

bc_data_end = bc_data_start + len(BAND_CMP['RC3']['feat']) - 1

chart_bc = wb.add_chart({'type': 'bar'})
for j, (series_name, col, color) in enumerate([
    ('RC3 Feature',    1, MID_BLUE),
    ('RC3 Unaffected', 2, '#9DC3E6'),
    ('RC4 Feature',    3, '#ED7D31'),
    ('RC4 Unaffected', 4, '#F4B183'),
]):
    chart_bc.add_series({
        'name': series_name,
        'categories': ['Band_Comparison', bc_data_start, 0, bc_data_end, 0],
        'values':     ['Band_Comparison', bc_data_start, col, bc_data_end, col],
        'fill': {'color': color},
        'gap': 60,
    })
chart_bc.set_title({'name': 'Δ% Comparison: Feature Bands vs Unaffected Bands'})
chart_bc.set_x_axis({'name': 'Delta % (Trial vs Baseline)', 'num_format': '0%', 'crossing': 0,
                      'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                      'line': {'color': '#666666'}})
chart_bc.set_y_axis({'name': '', 'line': {'none': True}})
chart_bc.set_legend({'position': 'bottom'})
chart_bc.set_size({'width': 680, 'height': 340})
chart_bc.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
ws4.insert_chart(bc_row, 6, chart_bc, {'x_offset': 5, 'y_offset': 5})

ws4.write(bc_data_end+2, 0,
    'Key insight: KPIs degraded on UNAFFECTED bands confirm a confounding network trend, not solely the CBXXXXXX feature.', note_f)


# ════════════════════════════════════════════════════════════════════════════
# SHEET 5: Per-Carrier Detail
# ════════════════════════════════════════════════════════════════════════════
ws5 = wb.add_worksheet('Per_Carrier_Detail')
ws5.set_tab_color('#70AD47')
ws5.set_zoom(85)
ws5.set_column('A:A', 18)
ws5.set_column('B:K', 11)

ws5.merge_range('A1:K1', 'Per-Carrier KPI Detail — Feature Bands (B800 / B900 / B1800 / B2100)', title_f)
ws5.set_row(0, 22)

CARRIERS  = ['B800', 'B900', 'B1800', 'B2100']
PC_CHARTS = [
    ('QCI8 Delay',  'ms',  PC_RC3, PC_RC4, True),
    ('Latency DL',  'ms',  PC_RC3, PC_RC4, True),
    ('DRX Sleep',   '%',   PC_RC3, PC_RC4, False),
    ('PSM Ratio',   '%',   PC_RC3, PC_RC4, False),
]

rpc = 2
for kname, unit, rc3dat, rc4dat, hib in PC_CHARTS:
    # Write sub-table
    ws5.merge_range(rpc, 0, rpc, 9, f'{kname} ({unit}) — Baseline vs Trial per Carrier', hdr_mid)
    ws5.set_row(rpc, 18)
    rpc += 1
    ws5.write(rpc, 0, 'Carrier', hdr)
    ws5.write(rpc, 1, 'RC3 Baseline', hdr)
    ws5.write(rpc, 2, 'RC3 Trial', hdr)
    ws5.write(rpc, 3, 'RC3 Δ%', hdr)
    ws5.write(rpc, 4, '', fmt(border=0))
    ws5.write(rpc, 5, 'RC4 Baseline', hdr)
    ws5.write(rpc, 6, 'RC4 Trial', hdr)
    ws5.write(rpc, 7, 'RC4 Δ%', hdr)
    rpc += 1

    tbl_start = rpc
    for carrier in CARRIERS:
        r3p = rc3dat.get(kname, {}).get(carrier)
        r4p = rc4dat.get(kname, {}).get(carrier)
        ws5.write(rpc, 0, carrier, ctr_f)
        if r3p:
            dp3 = (r3p[1]-r3p[0])/abs(r3p[0]) if r3p[0] else 0
            ws5.write(rpc, 1, r3p[0], num_f)
            ws5.write(rpc, 2, r3p[1], num_f)
            ws5.write(rpc, 3, dp3, delta_fmt(r3p[0],r3p[1],hib))
        else:
            ws5.write(rpc, 1, 'N/A', ctr_f)
            ws5.write(rpc, 2, 'N/A', ctr_f)
            ws5.write(rpc, 3, 'N/A', ctr_f)
        ws5.write(rpc, 4, '', fmt(border=0))
        if r4p:
            dp4 = (r4p[1]-r4p[0])/abs(r4p[0]) if r4p[0] else 0
            ws5.write(rpc, 5, r4p[0], num_f)
            ws5.write(rpc, 6, r4p[1], num_f)
            ws5.write(rpc, 7, dp4, delta_fmt(r4p[0],r4p[1],hib))
        else:
            ws5.write(rpc, 5, 'N/A', ctr_f)
            ws5.write(rpc, 6, 'N/A', ctr_f)
            ws5.write(rpc, 7, 'N/A', ctr_f)
        rpc += 1
    tbl_end = rpc - 1

    # Grouped bar chart: Baseline vs Trial per carrier
    chart_pc = wb.add_chart({'type': 'column'})
    for per_idx, (period, color) in enumerate(zip(
        ['RC3 Baseline', 'RC3 Trial', 'RC4 Baseline', 'RC4 Trial'],
        [DARK_BLUE, '#9DC3E6', '#ED7D31', '#F4B183']
    )):
        col_idx = [1, 2, 5, 6][per_idx]
        chart_pc.add_series({
            'name': period,
            'categories': ['Per_Carrier_Detail', tbl_start, 0, tbl_end, 0],
            'values':     ['Per_Carrier_Detail', tbl_start, col_idx, tbl_end, col_idx],
            'fill': {'color': color},
            'gap': 80,
        })
    chart_pc.set_title({'name': f'{kname} ({unit}) per Carrier — Baseline vs Trial'})
    chart_pc.set_x_axis({'name': 'Carrier', 'line': {'color': '#666666'}})
    chart_pc.set_y_axis({'name': f'{kname} ({unit})',
                          'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                          'line': {'color': '#666666'}})
    chart_pc.set_legend({'position': 'bottom'})
    chart_pc.set_size({'width': 480, 'height': 300})
    chart_pc.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
    ws5.insert_chart(tbl_start - 2, 9, chart_pc, {'x_offset': 5, 'y_offset': 5})

    rpc += 2  # gap before next KPI block


# ════════════════════════════════════════════════════════════════════════════
# SHEET 6: Delta% Ranking (sorted by significance)
# ════════════════════════════════════════════════════════════════════════════
ws6 = wb.add_worksheet('Significance_Ranking')
ws6.set_tab_color(ORANGE2)
ws6.set_zoom(85)
ws6.set_column('A:A', 22)
ws6.set_column('B:F', 11)

ws6.merge_range('A1:F1', 'KPI Significance Ranking — by |σ| (highest degradation first)', title_f)
ws6.set_row(0, 22)

# Combine RC3 + RC4 and sort by degradation sigma
all_kpis = []
for r3, r4 in zip(RC3_FEAT, RC4_FEAT):
    name3, tier3, hb3, bl3, tr3, pr3, sg3 = r3
    name4, tier4, hb4, bl4, tr4, pr4, sg4 = r4
    cs3 = calc_deg_sigma(sg3, hb3) if sg3 is not None else 0
    cs4 = calc_deg_sigma(sg4, hb4) if sg4 is not None else 0
    dp3 = (tr3-bl3)/abs(bl3) if bl3 else 0
    dp4 = (tr4-bl4)/abs(bl4) if bl4 else 0
    all_kpis.append((name3, tier3, cs3, dp3, cs4, dp4,
                     max(cs3, cs4)))  # rank by max degradation sigma

# Sort by max degradation (highest positive sigma first for bad KPIs)
all_kpis.sort(key=lambda x: -x[6])

ws6.write(1, 0, 'KPI', hdr)
ws6.write(1, 1, 'Tier', hdr)
ws6.write(1, 2, 'RC3 σ (deg+)', hdr)
ws6.write(1, 3, 'RC3 Δ%', hdr)
ws6.write(1, 4, 'RC4 σ (deg+)', hdr)
ws6.write(1, 5, 'RC4 Δ%', hdr)

rank_start = 2
for i, (name, tier, cs3, dp3, cs4, dp4, _) in enumerate(all_kpis):
    r = rank_start + i
    ws6.set_row(r, 16)
    # Determine degradation level from max sigma
    max_cs = max(cs3, cs4)
    hib = True  # all are "degradation positive" already
    bg = signif_bg(max_cs, True) if max_cs > 0.5 else (signif_bg(min(cs3,cs4), True) if min(cs3,cs4) < -0.5 else LGRAY)
    ws6.write(r, 0, name, fmt(align='left',valign='vcenter',bg_color=bg,
                               font_color='#FFFFFF' if max_cs>=2 else '#000000'))
    ws6.write(r, 1, tier, fmt(align='center',valign='vcenter',bg_color=bg,
                               font_color='#FFFFFF' if max_cs>=2 else MID_BLUE,bold=True))
    ws6.write(r, 2, cs3, fmt(num_format='0.0σ',align='center',valign='vcenter',
                               bg_color=signif_bg(cs3,True) if cs3 > 0.5 else LGRAY))
    ws6.write(r, 3, dp3, fmt(num_format='+0.0%;-0.0%;0.0%',align='center',valign='vcenter'))
    ws6.write(r, 4, cs4, fmt(num_format='0.0σ',align='center',valign='vcenter',
                               bg_color=signif_bg(cs4,True) if cs4 > 0.5 else LGRAY))
    ws6.write(r, 5, dp4, fmt(num_format='+0.0%;-0.0%;0.0%',align='center',valign='vcenter'))

rank_end = rank_start + len(all_kpis) - 1

# Sorted sigma chart
chart_rank = wb.add_chart({'type': 'bar'})
chart_rank.add_series({
    'name': 'RC3 σ',
    'categories': ['Significance_Ranking', rank_start, 0, rank_end, 0],
    'values':     ['Significance_Ranking', rank_start, 2, rank_end, 2],
    'fill': {'color': MID_BLUE}, 'gap': 60,
})
chart_rank.add_series({
    'name': 'RC4 σ',
    'categories': ['Significance_Ranking', rank_start, 0, rank_end, 0],
    'values':     ['Significance_Ranking', rank_start, 4, rank_end, 4],
    'fill': {'color': '#ED7D31'},
})
chart_rank.set_title({'name': 'KPI Significance Ranking (|σ| sorted, degradation = positive)'})
chart_rank.set_x_axis({'name': 'Sigma (normalised: degrad. positive)', 'crossing': 0,
                        'min': -6, 'max': 6,
                        'major_gridlines': {'visible': True, 'line': {'dash_type': 'dash', 'color': '#DDDDDD'}},
                        'line': {'color': '#666666'}})
chart_rank.set_y_axis({'name': '', 'line': {'none': True}})
chart_rank.set_legend({'position': 'bottom'})
chart_rank.set_size({'width': 680, 'height': 560})
chart_rank.set_chartarea({'border': {'color': '#AAAAAA'}, 'fill': {'color': '#FAFAFA'}})
ws6.insert_chart(1, 7, chart_rank, {'x_offset': 5, 'y_offset': 5})


wb.close()
print(f'Written: {OUT}')
