// =============================================================================
// NR TECHNICAL MEMO GENERATOR — ran-trial-production skill (5G NSA)
// =============================================================================
// STATUS: Phase 3 skeleton. Produces a valid .docx with NR NSA memo structure,
// ready to populate with real trial data. Adapted from scripts/lte/trial_memo_template.js
// with NSA-specific sections (SgNB, SCG fallback, EPS fallback) and removal of
// LTE-specific sections (H1/H2/H3 framework, feature/unaffected band tables).
//
// DEPENDENCIES:
//   npm install docx
//
// USAGE:
//   1. Replace TRIAL DATA blocks (search "=== TRIAL DATA ===") with real values
//   2. node trial_memo_nr.js
// OUTPUT:
//   <TRIAL_ID>_NR_Trial_Analysis.docx
// =============================================================================
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign
} = require('docx');
const fs = require('fs');

// ─── Colour palette (shared with LTE) ────────────────────────────────────────
const C = {
  darkBlue: '1F3864', midBlue: '2F5496', lightBlue: 'D5E8F0',
  red: 'C00000', orange: 'E26B0A', green: '375623',
  pass: 'E2EFDA', fail: 'FFDDD5', neutral: 'F2F2F2', warn: 'FFF2CC',
  white: 'FFFFFF', border: 'AAAAAA'
};
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const allBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cellPad = { top: 80, bottom: 80, left: 120, right: 120 };

// =============================================================================
// === TRIAL DATA ============================================================
// =============================================================================
const TRIAL_ID        = 'CBXXXXXX';                                    // ← EDIT: your trial ID
const FEATURE_NAME    = '<Feature name from Nokia DN>';               // ← EDIT
const FEATURE_PARAM   = '<parameter name>';                          // ← EDIT
const FEATURE_OLD_VAL = 'false';                                     // ← EDIT
const FEATURE_NEW_VAL = 'true';                                      // ← EDIT
const VERDICT         = 'PASS WITH CONDITIONS';                      // ← EDIT: PASS / PASS WITH CONDITIONS / FAIL / INCONCLUSIVE
const VERDICT_REASON  = '[to be filled in based on real trial data]'; // ← EDIT

const CARRIERS        = ['N28', 'N78_F1', 'N78_F2', 'N78_F3'];       // ← EDIT: your carrier labels
const BASELINE_PERIOD = 'YYYY-MM-DD → YYYY-MM-DD (N days)';          // ← EDIT
const TRIAL_PERIOD    = 'YYYY-MM-DD → YYYY-MM-DD (N days)';          // ← EDIT
const POST_RB_PERIOD  = null;  // ← EDIT: or "YYYY-MM-DD → YYYY-MM-DD" if rolled back

// Tier 1 KPIs — fill from extract_stats.py or the Statistical Analysis Excel
// Format: [KPI name, Baseline, Trial, Δ%, σ (chart), expected direction per PDF, higherIsBad]
const T1_KPIS = [
  ['<T1 KPI name>',   '0.00', '0.00', '0.00%', '0.00', '<expected direction>', false],
  // ← EDIT: add rows from your extract; see references/nr/kpi_column_map.md for tier classification
];

// Watchdog KPIs (Tier 3) — must not degrade; fill from Statistical Analysis Excel
// Format: [KPI name, Baseline, Trial, σ (chart), status]
const T3_KPIS = [
  ['<T3 KPI name>',   '0.00', '0.00', '0.00', 'OK'],
  // ← EDIT: add rows for Cell Availability, Accessibility SR, RACH SR, SgNB KPIs, etc.
];

// ES (cluster energy) — optional; integrate from ES report when available
const ES_KPIS = null;  // ← EDIT: set to array once ES report is integrated

// =============================================================================
// === GENERATION — edit below only to change structure =======================
// =============================================================================

const p = (children, opts = {}) => new Paragraph({ children, ...opts });
const t = (text, opts = {}) => new TextRun({ text, font: 'Arial', ...opts });
const h1 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, font: 'Arial', size: 32, bold: true })] });
const h2 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, font: 'Arial', size: 26, bold: true })] });
const h3 = (text) => new Paragraph({ heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, font: 'Arial', size: 22, bold: true, italics: true })] });
const body = (text, opts = {}) => p([t(text, { size: 20, ...opts })]);
const spacer = () => p([t('', { size: 20 })]);

function headerCell(text, w, shade = C.darkBlue) {
  return new TableCell({
    borders: allBorders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: cellPad, verticalAlign: VerticalAlign.CENTER,
    children: [p([t(text, { size: 18, bold: true, color: shade === C.darkBlue ? C.white : '000000' })])]
  });
}
function dataCell(text, w, shade = null, bold = false, align = AlignmentType.LEFT) {
  return new TableCell({
    borders: allBorders,
    width: { size: w, type: WidthType.DXA },
    shading: shade ? { fill: shade, type: ShadingType.CLEAR } : undefined,
    margins: cellPad,
    children: [p([t(text, { size: 18, bold })], { alignment: align })]
  });
}

// Verdict shade
function verdictShade(v) {
  if (v.startsWith('PASS')) return C.pass;
  if (v.startsWith('FAIL')) return C.fail;
  return C.warn;  // INCONCLUSIVE or PASS WITH CONDITIONS
}

// ─── Section 1 — Executive Summary ───────────────────────────────────────────
function section1() {
  return [
    h1('1. Executive Summary'),
    body(`Feature: ${FEATURE_NAME} (${TRIAL_ID}).`),
    body(`Parameter changed: ${FEATURE_PARAM} — ${FEATURE_OLD_VAL} → ${FEATURE_NEW_VAL}`),
    body(`Trial scope: NR NSA (EN-DC). Carriers: ${CARRIERS.join(', ')}.`),
    body(`Baseline: ${BASELINE_PERIOD}`),
    body(`Trial:    ${TRIAL_PERIOD}`),
    POST_RB_PERIOD ? body(`Post-RB:  ${POST_RB_PERIOD}`) : body('Post-RB:  not conducted'),
    spacer(),
    new Table({
      width: { size: 9500, type: WidthType.DXA },
      rows: [
        new TableRow({ children: [
          headerCell('Verdict', 3000),
          dataCell(VERDICT, 6500, verdictShade(VERDICT), true, AlignmentType.CENTER)
        ]}),
        new TableRow({ children: [
          headerCell('Reasoning', 3000),
          dataCell(VERDICT_REASON, 6500)
        ]}),
      ]
    }),
    spacer(),
  ];
}

// ─── Section 2 — Trial Description ───────────────────────────────────────────
function section2() {
  return [
    h1('2. Trial Description'),
    h2('2.1 Feature Objective'),
    body(`${FEATURE_NAME} (${TRIAL_ID}).` +
         ' [Fill in: brief feature objective from the Nokia DN — what the feature changes at the ' +
         'scheduling/hardware level and what the primary benefit is.]'),
    body('[Source: Nokia feature document <document number>, <title>, Issue <N>. Section <N>.]'), // ← EDIT
    spacer(),
    h2('2.2 Timeline'),
    body(`Baseline: ${BASELINE_PERIOD}`),
    body(`Trial:    ${TRIAL_PERIOD}`),
    POST_RB_PERIOD ? body(`Post-RB:  ${POST_RB_PERIOD}`) : spacer(),
    h2('2.3 Carrier Scope'),
    new Table({
      width: { size: 9500, type: WidthType.DXA },
      rows: [
        new TableRow({ children: [
          headerCell('Carrier', 2000),
          headerCell('NR Band', 2000),
          headerCell('NRARFCN', 2500),
          headerCell('Role', 3000),
        ]}),
        // ← EDIT: add one TableRow per carrier; set NRARFCN, band, and role
        new TableRow({ children: [
          dataCell('<carrier label>', 2000), dataCell('n<band>', 2000), dataCell('<NRARFCN>', 2500),
          dataCell('Feature', 3000, C.lightBlue)
        ]}),
      ]
    }),
    body(`All ${CARRIERS.length} carriers are in the feature scope. ${TRIAL_ID} applies uniformly ` +
         'across the cluster. There is no in-cluster unaffected-carrier control group.', { italics: true }),
    spacer(),
  ];
}

// ─── Section 3 — Data Quality Assessment ─────────────────────────────────────
function section3() {
  return [
    h1('3. Data Quality Assessment'),
    body('Data source: Nokia 5G System Program cluster-per-carrier export, daily granularity.'),
    body(`Baseline window: ${BASELINE_PERIOD.match(/\\((.*?)\\)/)?.[1] || '?'}`),
    body(`Trial window: ${TRIAL_PERIOD.match(/\\((.*?)\\)/)?.[1] || '?'}`),
    body(`Data completeness: all 4 carriers reporting for all days in both periods.`),
    spacer(),
    h3('Caveats specific to this analysis'),
    body('• No in-cluster unaffected-carrier control group. H1/H2/H3 hypothesis framework ' +
         'used for LTE is not applicable here.'),
    body('• External controls (neighbouring NR cluster outside the trial, LTE anchor-leg ' +
         'behaviour during the same window) were not in scope for this analysis. Concurrent ' +
         'network effects cannot be fully excluded from pre/post comparison alone.'),
    body('• A PASS verdict under these conditions should default to PASS WITH CONDITIONS ' +
         'unless an external control has been reviewed separately.'),
    body('• KPIs with ≥80% NaN across the analysis period (e.g. 5QI1 drop ratios at 93% NaN ' +
         'in the reference export) have been flagged or excluded — see Appendix.'),
    spacer(),
  ];
}

// ─── Section 4 — KPI Analysis ────────────────────────────────────────────────
function section4() {
  // T1 table
  const t1Rows = [new TableRow({ children: [
    headerCell('KPI', 2500),
    headerCell('Baseline', 1200),
    headerCell('Trial', 1200),
    headerCell('Δ%', 1200),
    headerCell('σ', 900),
    headerCell('Expected (per PDF)', 2500),
  ]})];
  for (const [name, bl, tr, delta, sigma, expected, hib] of T1_KPIS) {
    const sh = (sigma === 'n/a') ? C.neutral :
               (Math.abs(parseFloat(sigma)) >= 2 ? (parseFloat(sigma) > 0 === hib ? C.fail : C.pass) : C.neutral);
    t1Rows.push(new TableRow({ children: [
      dataCell(name, 2500),
      dataCell(bl, 1200, null, false, AlignmentType.RIGHT),
      dataCell(tr, 1200, null, false, AlignmentType.RIGHT),
      dataCell(delta, 1200, null, false, AlignmentType.RIGHT),
      dataCell(sigma, 900, sh, true, AlignmentType.CENTER),
      dataCell(expected, 2500, null, false, AlignmentType.LEFT),
    ]}));
  }

  // T3 table
  const t3Rows = [new TableRow({ children: [
    headerCell('KPI', 3500),
    headerCell('Baseline', 1500),
    headerCell('Trial', 1500),
    headerCell('σ', 1000),
    headerCell('Status', 2000),
  ]})];
  for (const [name, bl, tr, sigma, status] of T3_KPIS) {
    const sh = status === 'OK' ? C.pass :
               status.startsWith('FLAG') ? C.fail : C.warn;
    t3Rows.push(new TableRow({ children: [
      dataCell(name, 3500),
      dataCell(bl, 1500, null, false, AlignmentType.RIGHT),
      dataCell(tr, 1500, null, false, AlignmentType.RIGHT),
      dataCell(sigma, 1000, null, false, AlignmentType.CENTER),
      dataCell(status, 2000, sh, true, AlignmentType.CENTER),
    ]}));
  }

  return [
    h1('4. KPI Analysis'),
    h2('4.1 Primary KPIs (Tier 1)'),
    body(`KPIs classified Tier 1 based on ${TRIAL_ID} feature document predictions. ` +
         '[Fill in: Nokia DN number and relevant sections.]'),
    new Table({ width: { size: 9500, type: WidthType.DXA }, rows: t1Rows }),
    spacer(),
    body('INTERPRETATION: [placeholder — to be written per real trial]'),
    spacer(),
    h2('4.2 Watchdog KPIs (Tier 3)'),
    body(`KPIs that must not degrade under ${TRIAL_ID} activation:`),
    new Table({ width: { size: 9500, type: WidthType.DXA }, rows: t3Rows }),
    spacer(),
    body('INTERPRETATION: [placeholder — to be written per real trial]'),
    spacer(),
    h2('4.3 NSA-Specific — SgNB and EPS Fallback'),
    body('EN-DC-specific KPIs that behave only in NSA deployments:'),
    body('• SgNB addition preparation success ratio — [value]'),
    body('• SgNB reconfiguration success ratio — [value]'),
    body('• SgNB abnormal release ratio — [value]'),
    body('• Number of UE redirections to E-UTRAN (EPS fallback) — [value]'),
    body('• PSCell change success ratio — [value]'),
    spacer(),
    h2('4.4 Energy Saving Impact (Cluster Level)'),
    ES_KPIS
      ? body('ES report data integrated — see stats Excel for detailed sigma analysis.')
      : body('ES report not yet integrated into this memo version. Cluster-level energy ' +
             'analysis requires the ES cluster report and the ES column map in ' +
             'kpi_column_map.md to be finalised. Placeholder section — populate once available.'),
    spacer(),
  ];
}

// ─── Section 5 — Confounding factors ─────────────────────────────────────────
function section5() {
  return [
    h1('5. Confounding Factor Assessment'),
    body('• Traffic load: [reviewed / not reviewed — add Avg NSA Users trend]'),
    body('• Software upgrades: [none known / list here]'),
    body('• Hardware changes: [none known / list here]'),
    body('• Neighbour changes: [none known / list here]'),
    body('• Other concurrent feature activations: [list any features activated in the same window. ' +
         'If this feature has a prerequisite feature, note whether it was already active or ' +
         'co-activated — in which case the observed effects are the combined result.]'),
    spacer(),
  ];
}

// ─── Section 6 — Verdict ──────────────────────────────────────────────────────
function section6() {
  return [
    h1('6. Verdict and Recommendation'),
    new Table({
      width: { size: 9500, type: WidthType.DXA },
      rows: [
        new TableRow({ children: [
          headerCell('Verdict', 3000),
          dataCell(VERDICT, 6500, verdictShade(VERDICT), true, AlignmentType.CENTER)
        ]}),
        new TableRow({ children: [
          headerCell('Reasoning', 3000),
          dataCell(VERDICT_REASON, 6500)
        ]}),
        new TableRow({ children: [
          headerCell('Recommendation', 3000),
          dataCell('[placeholder — roll out / extend / revert / collect more data]', 6500)
        ]}),
      ]
    }),
    spacer(),
  ];
}

// ─── Section 7 — Appendix ─────────────────────────────────────────────────────
function section7() {
  return [
    h1('7. Appendix'),
    body('• Full KPI summary CSV: see extract_stats.py output'),
    body('• Per-carrier trend charts: see <TRIAL_ID>_NR_KPI_Grouped.xlsx'),
    body('• Full sigma ranking: see <TRIAL_ID>_NR_Statistical_Analysis.xlsx, ' +
         'sheet Significance_Ranking'),
    body('• Feature specification: Nokia <document number>, <title>, Issue <N> (<date>), Section <N>'), // ← EDIT
    body('• Methodology: references/nr/methodology_nr.md'),
    body('• KPI column classification: references/nr/kpi_column_map.md'),
    spacer(),
  ];
}

// ─── Document assembly ────────────────────────────────────────────────────────
const doc = new Document({
  styles: { default: { document: { run: { font: 'Arial', size: 20 } } } },
  sections: [{
    properties: {},
    children: [
      h1(`${TRIAL_ID} NR Trial Analysis — ${FEATURE_NAME}`),
      spacer(),
      ...section1(),
      ...section2(),
      ...section3(),
      ...section4(),
      ...section5(),
      ...section6(),
      ...section7(),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  const outPath = `./${TRIAL_ID}_NR_Trial_Analysis.docx`;
  fs.writeFileSync(outPath, buf);
  console.log(`[saved] ${outPath}`);
}).catch(err => {
  console.error('[error]', err);
  process.exit(1);
});
