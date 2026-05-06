// =============================================================================
// TECHNICAL MEMO GENERATOR — ran-trial-production skill template
// =============================================================================
// REFERENCE TRIAL: CBXXXXXX (allowTrafficConcentration=0, MNO 4G, RC3/RC4)
//
// DEPENDENCIES: npm install docx  (run in the script's directory)
//
// TO ADAPT FOR A NEW TRIAL:
//   Search for "=== TRIAL DATA ===" blocks — these are the only sections to change.
//   Everything else (formatting, structure, section numbers) stays fixed.
//
//   Key substitutions:
//     TRIAL_ID          → your trial identifier (e.g. CB010999)
//     FEATURE_NAME      → parameter name changed
//     FEATURE_BANDS     → comma-separated band list (e.g. B800, B900, B1800, B2100)
//     UNAFFECTED_BANDS  → comma-separated list (e.g. B700, B2300_F1, B2300_F2)
//     VERDICT           → PASS / PASS WITH CONDITIONS / INCONCLUSIVE / FAIL
//     All KPI values in tables (search for hard-coded numbers)
//     Sigma values in appendix tables
//     H1/H2/H3 conclusion text in Section 4.3
//
// RUN: node trial_memo_template.js
// OUTPUT: <TRIAL_ID>_Trial_Analysis.docx
// =============================================================================
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  Header, Footer, AlignmentType, HeadingLevel, BorderStyle, WidthType,
  ShadingType, VerticalAlign, PageNumber, LevelFormat, PageBreak
} = require('docx');
const fs = require('fs');

// ─── Colour palette ──────────────────────────────────────────
const C = {
  darkBlue: '1F3864', midBlue: '2F5496', lightBlue: 'D5E8F0',
  red: 'C00000', orange: 'E26B0A', green: '375623',
  pass: 'E2EFDA', fail: 'FFDDD5', neutral: 'F2F2F2', warn: 'FFF2CC',
  white: 'FFFFFF', border: 'AAAAAA'
};

// ─── Reusable border ─────────────────────────────────────────
const thinBorder = { style: BorderStyle.SINGLE, size: 1, color: C.border };
const allBorders = { top: thinBorder, bottom: thinBorder, left: thinBorder, right: thinBorder };
const cellPad = { top: 80, bottom: 80, left: 120, right: 120 };

// ─── Helpers ─────────────────────────────────────────────────
const p = (children, opts = {}) => new Paragraph({ children, ...opts });
const t = (text, opts = {}) => new TextRun({ text, font: 'Arial', ...opts });
const h1 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_1,
  children: [new TextRun({ text, font: 'Arial', size: 32, bold: true })]
});
const h2 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_2,
  children: [new TextRun({ text, font: 'Arial', size: 26, bold: true })]
});
const h3 = (text) => new Paragraph({
  heading: HeadingLevel.HEADING_3,
  children: [new TextRun({ text, font: 'Arial', size: 22, bold: true, italics: true })]
});
const body = (text, opts = {}) => p([t(text, { size: 20, ...opts })]);
const bullet = (text, opts = {}) => new Paragraph({
  numbering: { reference: 'bullets', level: 0 },
  children: [t(text, { size: 20, ...opts })]
});
const spacer = () => p([t('', { size: 20 })]);

// ─── Table helpers ────────────────────────────────────────────
function headerCell(text, w, shade = C.darkBlue) {
  return new TableCell({
    borders: allBorders,
    width: { size: w, type: WidthType.DXA },
    shading: { fill: shade, type: ShadingType.CLEAR },
    margins: cellPad,
    verticalAlign: VerticalAlign.CENTER,
    children: [p([t(text, { size: 18, bold: true, color: shade === C.darkBlue ? C.white : '000000' })])]
  });
}
function dataCell(text, w, shade = null, bold = false, color = '000000', align = AlignmentType.LEFT) {
  return new TableCell({
    borders: allBorders,
    width: { size: w, type: WidthType.DXA },
    shading: shade ? { fill: shade, type: ShadingType.CLEAR } : undefined,
    margins: cellPad,
    children: [p([t(text, { size: 18, bold, color })], { alignment: align })]
  });
}

// Delta colouring helper: red if degradation, green if improvement, grey if neutral
// For most KPIs: positive % = worse (e.g. BLER, drop ratio), negative % = better
// For success/availability rates: negative = worse, positive = better
function deltaShade(pct, higherIsBad = true) {
  if (Math.abs(pct) < 1.0) return C.neutral;
  if (higherIsBad) {
    return pct > 0 ? C.fail : C.pass;
  } else {
    return pct < 0 ? C.fail : C.pass;
  }
}

// ─── Main document ────────────────────────────────────────────
const doc = new Document({
  numbering: {
    config: [
      {
        reference: 'bullets',
        levels: [{ level: 0, format: LevelFormat.BULLET, text: '\u2022',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }]
      },
      {
        reference: 'numbers',
        levels: [{ level: 0, format: LevelFormat.DECIMAL, text: '%1.',
          alignment: AlignmentType.LEFT,
          style: { paragraph: { indent: { left: 720, hanging: 360 } } } }]
      }
    ]
  },
  styles: {
    default: {
      document: { run: { font: 'Arial', size: 20 } }
    },
    paragraphStyles: [
      { id: 'Heading1', name: 'Heading 1', basedOn: 'Normal', next: 'Normal',
        run: { size: 32, bold: true, font: 'Arial', color: C.darkBlue },
        paragraph: { spacing: { before: 320, after: 160 }, outlineLevel: 0,
          border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: C.midBlue, space: 4 } } } },
      { id: 'Heading2', name: 'Heading 2', basedOn: 'Normal', next: 'Normal',
        run: { size: 26, bold: true, font: 'Arial', color: C.midBlue },
        paragraph: { spacing: { before: 240, after: 120 }, outlineLevel: 1 } },
      { id: 'Heading3', name: 'Heading 3', basedOn: 'Normal', next: 'Normal',
        run: { size: 22, bold: true, italics: true, font: 'Arial', color: '000000' },
        paragraph: { spacing: { before: 180, after: 80 }, outlineLevel: 2 } },
    ]
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 }
      }
    },
    headers: {
      default: new Header({
        children: [
          new Paragraph({
            children: [
              t('CBXXXXXX — Autonomous FDD LTE Micro-DTX | Trial Analysis Report', { size: 16, color: '888888' }),
              t('\tCONFIDENTIAL', { size: 16, color: 'C00000', bold: true })
            ],
            tabStops: [{ type: 'right', position: 9360 }],
            border: { bottom: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC', space: 4 } }
          })
        ]
      })
    },
    footers: {
      default: new Footer({
        children: [
          new Paragraph({
            children: [
              t('Nokia 4G LTE RAN Trial — MNO Network  |  Analysis date: 18-Mar-2026  |  ', { size: 16, color: '888888' }),
              t('Page ', { size: 16, color: '888888' }),
              new TextRun({ children: [PageNumber.CURRENT], size: 16, color: '888888' })
            ],
            border: { top: { style: BorderStyle.SINGLE, size: 2, color: 'CCCCCC', space: 4 } }
          })
        ]
      })
    },
    children: [

      // ═══════════════════════════════════════════════════════
      // TITLE BLOCK
      // ═══════════════════════════════════════════════════════
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 240, after: 80 },
        shading: { fill: C.darkBlue, type: ShadingType.CLEAR },
        children: [t('TECHNICAL ANALYSIS MEMO', { size: 28, bold: true, color: C.white, font: 'Arial' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 40 },
        shading: { fill: C.darkBlue, type: ShadingType.CLEAR },
        children: [t('CBXXXXXX : Autonomous FDD LTE Micro-DTX without Traffic Concentration', { size: 24, bold: true, color: 'C7D9ED', font: 'Arial' })]
      }),
      new Paragraph({
        alignment: AlignmentType.CENTER,
        spacing: { before: 0, after: 320 },
        shading: { fill: C.darkBlue, type: ShadingType.CLEAR },
        children: [t('Trial Implementation 04-Feb-2026  |  Rollback 03-Mar-2026  |  Prepared 18-Mar-2026', { size: 18, color: 'A0B8D0', font: 'Arial' })]
      }),

      // ═══════════════════════════════════════════════════════
      // 1. EXECUTIVE SUMMARY
      // ═══════════════════════════════════════════════════════
      h1('1. Executive Summary'),

      // Verdict box
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2000, 8080],
        rows: [
          new TableRow({
            children: [
              headerCell('VERDICT', 2000),
              new TableCell({
                borders: allBorders,
                width: { size: 8080, type: WidthType.DXA },
                shading: { fill: C.fail, type: ShadingType.CLEAR },
                margins: cellPad,
                children: [p([t('FAIL  —  Rollback was correct. Feature should not be deployed.', { size: 22, bold: true, color: C.red })])]
              })
            ]
          })
        ]
      }),
      spacer(),

      body('Trial CBXXXXXX evaluated the behaviour of the μDTX feature when traffic concentration (TC) was disabled via LNCEL/allowTrafficConcentration = 0. The stated hypothesis was that removing TC would (a) maintain or improve power saving through more flexible DTX opportunities and (b) reduce scheduling latency by eliminating TC-induced muting delays on DL data.'),
      spacer(),
      body('Neither objective was achieved. The primary KPIs showed no meaningful improvement. Simultaneously, multiple watchdog KPIs degraded in a statistically significant and operationally material manner. The evidence is consistent across both tested software releases (RC3 and RC4), which strengthens the conclusion.'),
      spacer(),

      body('Band scope: allowTrafficConcentration = 0 was applied only to B800, B900, B1800, and B2100 layers. B700 and B2300 (F1/F2) were not part of the parameter change and serve as an impact-check reference. All primary KPI conclusions below are driven by the four feature bands.', { bold: true }),
      spacer(),
      body('Key findings at a glance:', { bold: true }),
      bullet('Power saving — feature bands: slight directional improvement (PSM +1.9% RC3, +0.6% RC4; ReducedTX +2.3% both RCs), but all deltas below 0.6σ and within baseline noise. PRIMARY OBJECTIVE NOT MET.'),
      bullet('DL Latency — feature bands: consistent small reduction in QCI8 delay (~−1.5 to −2.0%, −0.6σ) and average DL latency (~−1.8%, −1.0σ) in both RCs; insufficient to claim statistical significance. QCI1 VoLTE delay unchanged. PRIMARY OBJECTIVE NOT MET.'),
      bullet('UL Residual BLER — feature bands: significant in RC3 (+4.7%, +2.3σ), directional in RC4 (+1.8%, +0.7σ). Cross-RC inconsistency noted; RC3 result is the stronger signal.'),
      bullet('E-RAB Retainability — feature bands: RC3 degraded +25.4% (+3.7σ); RC4 only +4.6% (+0.2σ — not significant). IMPORTANT: parallel degradation also occurred on unaffected bands (RC3 +36.3%, RC4 +32.0%), suggesting a confounding network trend alongside any feature contribution.'),
      bullet('RC4 B2300_F1/F2 accessibility crash (UNAFFECTED BAND — parameter was NOT changed): RRC SR dropped 1.3–1.9pp; failure rate 5–9×. This is RC4 software-version specific and does not implicate the CBXXXXXX parameter directly.'),
      bullet('RC4 Intra-eNB HO success — feature bands: B1800 −2.3pp (−3.2σ). B700 also degraded (−2.8pp) but B700 is an unaffected band — likely RC4 software-version interaction.'),
      spacer(),

      body('The rollback on 03-Mar-2026 was appropriate. The feature failed to meet both primary objectives. RC3 feature-band watchdog degradation (UL rBLER +2.3σ, retainability +3.7σ) justified the decision. The parallel retainability deterioration on unaffected bands in both RCs signals a concurrent network health trend that must be investigated independently of the trial.'),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 2. TRIAL DESCRIPTION
      // ═══════════════════════════════════════════════════════
      new Paragraph({ children: [new PageBreak()] }),
      h1('2. Trial Description'),

      h2('2.1 Objective'),
      body('The CBXXXXXX feature enables μDTX to operate in scenarios where traffic concentration is not used. In the legacy (TC-enabled) scenario, the DL scheduler is restricted to "non-muted" subframes defined by the concentration pattern, which introduces additional DL buffering latency for low-load periods while providing a defined energy-saving gain. Disabling TC (allowTrafficConcentration = 0) was expected to:'),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Preserve or improve power saving by giving the PA more opportunities for DTX across all subframes', { size: 20 })] }),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Reduce DL scheduling latency by eliminating the muting pattern that holds back buffered data', { size: 20 })] }),
      spacer(),

      h2('2.2 Parameter Change'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [3500, 2000, 2000, 2580],
        rows: [
          new TableRow({ children: [headerCell('Parameter Path', 3500), headerCell('Before (Baseline)', 2000), headerCell('During Trial', 2000), headerCell('After Rollback', 2580)] }),
          new TableRow({ children: [
            dataCell('MRBTS/LNBTS/LNCEL/allowTrafficConcentration', 3500, C.neutral),
            dataCell('1 (enabled)', 2000, C.pass),
            dataCell('0 (disabled)', 2000, C.fail),
            dataCell('1 (re-enabled)', 2580, C.pass)
          ]})
        ]
      }),
      spacer(),

      h2('2.3 Trial Cluster'),
      body('Nokia 4G LTE network. MNO-operated carriers only. Two parallel software versions evaluated:'),
      bullet('RC3: 4G_System_Program_Nokia_20260128_20260316_RC3.xlsx'),
      bullet('RC4: 4G_System_Program_Nokia_20260128_20260316_RC4.xlsx'),
      body('All seven MNO carriers are present in the dataset: B700 (9260), B800 (6400), B900 (3725), B1800 (1226), B2100 (347), B2300_F1 (39250), B2300_F2 (39448). Non-MNO rows (Other MNO, NB-IoT) excluded before aggregation.'),
      spacer(),
      body('Parameter change scope — critical for analysis:', { bold: true }),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2000, 2200, 2200, 3680],
        rows: [
          new TableRow({ children: [headerCell('Group', 2000), headerCell('Carriers', 2200), headerCell('allowTrafficConcentration', 2200), headerCell('Role in Analysis', 3680)] }),
          new TableRow({ children: [
            dataCell('Feature bands', 2000, C.warn),
            dataCell('B800, B900, B1800, B2100', 2200),
            dataCell('Changed: 1 → 0', 2200, C.fail),
            dataCell('Primary analysis — feature effects measured here', 3680, C.lightBlue)
          ]}),
          new TableRow({ children: [
            dataCell('Unaffected bands', 2000, C.neutral),
            dataCell('B700, B2300_F1, B2300_F2', 2200),
            dataCell('Unchanged: 1 (kept enabled)', 2200, C.pass),
            dataCell('Impact check — should show no feature-driven change; deviations indicate confounders', 3680)
          ]}),
        ]
      }),
      body('Any KPI change observed on unaffected bands during the trial period cannot be attributed to CBXXXXXX and represents either a confounding network event or RC4 software-version specific behaviour.', { italics: true }),
      spacer(),

      h2('2.4 Trial Timeline'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2500, 2000, 2000, 3580],
        rows: [
          new TableRow({ children: [headerCell('Period', 2500), headerCell('Start', 2000), headerCell('End', 2000), headerCell('Duration', 3580)] }),
          new TableRow({ children: [dataCell('Baseline', 2500, C.neutral), dataCell('28-Jan-2026', 2000), dataCell('03-Feb-2026', 2000), dataCell('7 days  ⚠ SHORT — see Section 3.1', 3580, C.warn)] }),
          new TableRow({ children: [dataCell('Trial (TC disabled)', 2500, C.warn), dataCell('04-Feb-2026', 2000), dataCell('02-Mar-2026', 2000), dataCell('27 days', 3580)] }),
          new TableRow({ children: [dataCell('Post-rollback', 2500, C.neutral), dataCell('03-Mar-2026', 2000), dataCell('15-Mar-2026', 2000), dataCell('13 days', 3580)] }),
        ]
      }),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 3. DATA QUALITY
      // ═══════════════════════════════════════════════════════
      new Paragraph({ children: [new PageBreak()] }),
      h1('3. Data Quality Assessment'),

      h2('3.1 Baseline Period Length — Critical Limitation'),
      body('The baseline period spans only 7 calendar days (28-Jan to 03-Feb). This is a significant analytical constraint: the standard deviation of a 7-day window is inherently less reliable than a 4-week baseline. Several metrics (e.g. E-RAB Retainability, RACH SR) show daily variance that, across only 7 samples, could produce a misleading baseline mean. As a result, sigma calculations in this report should be interpreted with caution — they are indicative, not definitive. Where the observed deltas are large (>5σ), the conclusion holds even accounting for baseline uncertainty. Where they are 1–3σ, the result is directional but not statistically definitive.'),
      spacer(),

      h2('3.2 Traffic Load Consistency'),
      body('Traffic load was assessed via Average RRC Connected UEs and DL PRB Utilisation. Both remained stable across periods, confirming that load-driven KPI changes can be substantially excluded as a confounder:'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [3200, 1600, 1600, 1600, 2080],
        rows: [
          new TableRow({ children: [headerCell('Metric', 3200), headerCell('Baseline', 1600), headerCell('Trial', 1600), headerCell('Post-RB', 1600), headerCell('Comment', 2080)] }),
          new TableRow({ children: [dataCell('RC3 — Avg RRC Connected UEs', 3200, C.neutral), dataCell('13.6', 1600), dataCell('13.5', 1600), dataCell('14.2', 1600), dataCell('Stable', 2080, C.pass)] }),
          new TableRow({ children: [dataCell('RC3 — DL PRB Utilisation (%)', 3200, C.neutral), dataCell('18.0%', 1600), dataCell('17.8%', 1600), dataCell('18.2%', 1600), dataCell('Stable (−1.0%)', 2080, C.pass)] }),
          new TableRow({ children: [dataCell('RC4 — Avg RRC Connected UEs', 3200, C.neutral), dataCell('15.1', 1600), dataCell('14.9', 1600), dataCell('15.6', 1600), dataCell('Stable', 2080, C.pass)] }),
          new TableRow({ children: [dataCell('RC4 — DL PRB Utilisation (%)', 3200, C.neutral), dataCell('20.3%', 1600), dataCell('20.0%', 1600), dataCell('20.8%', 1600), dataCell('Stable (−1.8%)', 2080, C.pass)] }),
          new TableRow({ children: [dataCell('RC4 — Total RRC Attempts', 3200, C.neutral), dataCell('15.06M', 1600), dataCell('14.23M', 1600), dataCell('13.70M', 1600), dataCell('−5.5% (slightly lighter load during trial)', 2080, C.warn)] }),
        ]
      }),
      spacer(),
      body('Note: RC4 showed a 5.5% reduction in RRC connection attempts during the trial period. This is a minor loading reduction, not an increase — meaning any accessibility degradations observed in RC4 cannot be attributed to increased demand. The degradations are therefore more likely configuration-related.'),
      spacer(),

      h2('3.3 UL Latency Data Gap'),
      body('The "Average Latency Uplink" column returned 0.000 for all rows across both files. This metric is not populated in this KPI export. UL latency cannot be assessed from the available data, which is a gap against the trial objective.'),
      spacer(),

      h2('3.4 PSM Ratio Coverage'),
      body('The Cell in Power Saving Mode Ratio is non-zero only for B900, B1800, and B2300_F2. B700, B800, B2100, and B2300_F1 report 0% for all periods. This suggests the PSM feature is not licensed or configured on those carriers. Within the feature bands, only B900 and B1800 contribute to PSM Ratio measurements; B800 and B2100 show 0 throughout. ReducedTX Power Saving Mode is active on B2100 (and B2300_F2 in the unaffected group) but not B800, B900, or B1800. This limits inter-carrier comparisons for power saving but does not prevent period-over-period assessment within each band.'),
      spacer(),

      h2('3.5 External Events'),
      body('No information was provided on hardware interventions, software changes beyond RC versioning, or planned events. The consistency of degradation patterns across RC3 and RC4 (two independent SW builds running simultaneously) significantly reduces the likelihood of a single hardware failure or accidental misconfiguration being the root cause. The most parsimonious explanation for cross-RC consistency is that the trial parameter change itself drove the observed changes.'),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 4. KPI ANALYSIS
      // ═══════════════════════════════════════════════════════
      new Paragraph({ children: [new PageBreak()] }),
      h1('4. KPI Analysis'),

      h2('4.1 Tier 1 — Primary KPIs (Trial Objectives)'),

      h3('4.1.1 Power Saving'),
      body('The trial aimed to demonstrate maintained or improved power saving when TC is disabled. The table below shows feature-band aggregate values (B800 + B900 + B1800 + B2100) — the bands where the parameter was actually changed. A separate impact-check row shows unaffected bands (B700 + B2300_F1 + B2300_F2) for comparison.'),
      spacer(),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2500, 800, 1000, 1000, 1000, 1100, 800, 1880],
        rows: [
          new TableRow({ children: [
            headerCell('KPI', 2500), headerCell('RC', 800),
            headerCell('Baseline', 1000), headerCell('Trial', 1000),
            headerCell('Post-RB', 1000), headerCell('Delta', 1100),
            headerCell('Sigma', 800), headerCell('Assessment', 1880)
          ]}),
          // Feature band sub-header
          new TableRow({ children: [
            new TableCell({ borders: allBorders, width: { size: 2500, type: WidthType.DXA }, shading: { fill: C.lightBlue, type: ShadingType.CLEAR }, margins: cellPad, columnSpan: 8,
              children: [p([t('FEATURE BANDS — B800 / B900 / B1800 / B2100 (parameter changed)', { size: 18, bold: true, color: C.midBlue })])] })
          ]}),
          new TableRow({ children: [
            dataCell('PSM Ratio (%) — active: B900, B1800', 2500, C.neutral),
            dataCell('RC3', 800), dataCell('15.20', 1000), dataCell('15.49', 1000),
            dataCell('15.81', 1000), dataCell('+0.29 / +1.9%', 1100, C.neutral), dataCell('+0.5σ', 800),
            dataCell('Directional improvement — sub-1σ, noise', 1880, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('PSM Ratio (%) — active: B900, B1800', 2500, C.neutral),
            dataCell('RC4', 800), dataCell('14.21', 1000), dataCell('14.29', 1000),
            dataCell('13.99', 1000), dataCell('+0.08 / +0.6%', 1100, C.neutral), dataCell('+0.1σ', 800),
            dataCell('No change', 1880, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('ReducedTX Ratio (%) — active: B2100', 2500, C.neutral),
            dataCell('RC3', 800), dataCell('8.12', 1000), dataCell('8.30', 1000),
            dataCell('8.40', 1000), dataCell('+0.18 / +2.3%', 1100, C.neutral), dataCell('+0.6σ', 800),
            dataCell('Directional improvement — sub-1σ, noise', 1880, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('ReducedTX Ratio (%) — active: B2100', 2500, C.neutral),
            dataCell('RC4', 800), dataCell('6.86', 1000), dataCell('7.03', 1000),
            dataCell('7.02', 1000), dataCell('+0.17 / +2.4%', 1100, C.neutral), dataCell('+0.5σ', 800),
            dataCell('Directional improvement — sub-1σ, noise', 1880, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('DRX Sleep Ratio (%)', 2500, C.neutral),
            dataCell('RC3', 800), dataCell('63.85', 1000), dataCell('63.80', 1000),
            dataCell('64.38', 1000), dataCell('−0.05 / −0.1%', 1100, C.neutral), dataCell('−0.2σ', 800),
            dataCell('No change', 1880, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('DRX Sleep Ratio (%)', 2500, C.neutral),
            dataCell('RC4', 800), dataCell('65.43', 1000), dataCell('65.71', 1000),
            dataCell('66.32', 1000), dataCell('+0.28 / +0.4%', 1100, C.neutral), dataCell('+1.8σ', 800),
            dataCell('Borderline — marginal DRX improvement', 1880, C.neutral)
          ]}),
          // Unaffected band sub-header
          new TableRow({ children: [
            new TableCell({ borders: allBorders, width: { size: 2500, type: WidthType.DXA }, shading: { fill: C.neutral, type: ShadingType.CLEAR }, margins: cellPad, columnSpan: 8,
              children: [p([t('UNAFFECTED BANDS — B700 / B2300_F1 / B2300_F2 (parameter unchanged — impact check)', { size: 18, bold: true, color: '888888' })])] })
          ]}),
          new TableRow({ children: [
            dataCell('PSM Ratio — B2300_F2 active', 2500, C.neutral),
            dataCell('RC3', 800), dataCell('11.85', 1000), dataCell('10.98', 1000),
            dataCell('10.74', 1000), dataCell('−0.87 / −7.3%', 1100, C.warn), dataCell('−2.0σ', 800),
            dataCell('Degraded on unaffected band — confirms confounding factor', 1880, C.warn)
          ]}),
          new TableRow({ children: [
            dataCell('PSM Ratio — B2300_F2 active', 2500, C.neutral),
            dataCell('RC4', 800), dataCell('9.98', 1000), dataCell('10.07', 1000),
            dataCell('9.67', 1000), dataCell('+0.10 / +1.0%', 1100, C.neutral), dataCell('+0.3σ', 800),
            dataCell('Stable — no impact', 1880, C.neutral)
          ]}),
        ]
      }),
      spacer(),
      body('The feature bands show a slight directional improvement in PSM and ReducedTX ratios (+1.9–2.4%) but none of these reach 1σ significance. DRX Sleep Ratio was essentially unchanged. The RC3 B2300_F2 PSM decline (−7.3%, −2.0σ) on an UNAFFECTED band confirms that a confounding factor was present during the trial period independent of the CBXXXXXX parameter.'),
      body('Verdict: PRIMARY OBJECTIVE NOT MET — no statistically meaningful power saving benefit on the feature bands.', { bold: true }),
      spacer(),

      h3('4.1.2 DL Latency and PDCP SDU Delay — QCI1 (VoLTE) and QCI8 (Primary Data Bearer)'),
      body('Bearer mix verification (Step 2.5): Before interpreting delay metrics, the dominant QCI was identified from E-RAB Setup Attempts in the source data:'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [1800, 2200, 2200, 2200, 1680],
        rows: [
          new TableRow({ children: [headerCell('QCI', 1800), headerCell('E-RAB Attempts (total)', 2200), headerCell('DL Throughput Share', 2200), headerCell('Service Type', 2200), headerCell('Analysis Role', 1680)] }),
          new TableRow({ children: [dataCell('QCI 1', 1800, C.neutral), dataCell('30,813,072', 2200), dataCell('not split in report', 2200), dataCell('GBR VoLTE — voice', 2200), dataCell('Primary (latency-critical)', 1680, C.lightBlue)] }),
          new TableRow({ children: [dataCell('QCI 5', 1800, C.neutral), dataCell('1,748,944,932', 2200), dataCell('5.9%', 2200), dataCell('Non-GBR IMS signalling', 2200), dataCell('Context only', 1680)] }),
          new TableRow({ children: [dataCell('QCI 8', 1800, C.neutral), dataCell('2,279,262,427', 2200, C.lightBlue), dataCell('54.3%', 2200, C.lightBlue), dataCell('Non-GBR operator data', 2200, C.lightBlue), dataCell('PRIMARY DATA BEARER', 1680, C.lightBlue)] }),
          new TableRow({ children: [dataCell('QCI 9', 1800, C.neutral), dataCell('60,593,757', 2200), dataCell('39.9%', 2200), dataCell('Non-GBR default bearer', 2200), dataCell('Secondary context', 1680)] }),
        ]
      }),
      spacer(),
      body('QCI8 is unambiguously the primary data bearer: highest E-RAB attempt volume (2.28 billion, 4× more than QCI9) and 54.3% of DL scheduled throughput. QCI1 carries VoLTE and is the most latency-sensitive bearer regardless of volume. The latency analysis therefore focuses on QCI1 and QCI8. QCI9 is included as secondary context; QCI5 (IMS signalling, <6% throughput) is noted where statistically significant.'),
      spacer(),
      body('The trial hypothesis stated that removing TC muting would reduce DL scheduling latency. The analysis below uses feature-band aggregate values only (B800/B900/B1800/B2100). Average DL latency on feature bands showed consistent small reductions (~−1.8%, −1.0σ) in both RCs. QCI8 per-carrier breakdown is consistent: B800 −1.4%/−2.5%, B900 −1.6%/−1.9%, B1800 −2.5%/−1.5%, B2100 −2.0%/−1.6% (RC3/RC4 respectively). The direction is consistent but the magnitude in all cases falls within baseline day-to-day variance.'),
      spacer(),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2400, 700, 900, 900, 900, 1100, 700, 2480],
        rows: [
          new TableRow({ children: [
            headerCell('KPI', 2400), headerCell('RC', 700),
            headerCell('Baseline', 900), headerCell('Trial', 900),
            headerCell('Post-RB', 900), headerCell('Delta', 1100),
            headerCell('Sigma', 700), headerCell('Assessment', 2480)
          ]}),
          // --- PRIMARY: QCI1 and QCI8 ---
          new TableRow({ children: [
            new TableCell({ borders: allBorders, width: { size: 2400, type: WidthType.DXA }, shading: { fill: C.lightBlue, type: ShadingType.CLEAR }, margins: cellPad, columnSpan: 8,
              children: [p([t('PRIMARY BEARERS — QCI1 (VoLTE) and QCI8 (dominant data)', { size: 18, bold: true, color: C.midBlue })])] })
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI1 — VoLTE (ms)', 2400, C.neutral), dataCell('RC3', 700),
            dataCell('10.63', 900), dataCell('10.63', 900), dataCell('10.79', 900),
            dataCell('0.0 / 0.0%', 1100, C.neutral), dataCell('0.0σ', 700),
            dataCell('No change. VoLTE delay unaffected.', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI1 — VoLTE (ms)', 2400, C.neutral), dataCell('RC4', 700),
            dataCell('10.43', 900), dataCell('10.44', 900), dataCell('10.51', 900),
            dataCell('+0.02 / +0.2%', 1100, C.neutral), dataCell('~0σ', 700),
            dataCell('No change. VoLTE delay unaffected.', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI8 — primary data (ms)', 2400, C.neutral), dataCell('RC3', 700),
            dataCell('118.0', 900), dataCell('115.9', 900), dataCell('117.0', 900),
            dataCell('−2.1ms / −1.7%', 1100, C.neutral), dataCell('−0.6σ', 700),
            dataCell('Consistent −1.4 to −2.5% per carrier; within noise.', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI8 — primary data (ms)', 2400, C.neutral), dataCell('RC4', 700),
            dataCell('157.0', 900), dataCell('153.9', 900), dataCell('156.4', 900),
            dataCell('−3.1ms / −2.0%', 1100, C.neutral), dataCell('−0.6σ', 700),
            dataCell('Consistent −1.5 to −2.5% per carrier; within noise.', 2480, C.neutral)
          ]}),
          // --- SECONDARY CONTEXT ---
          new TableRow({ children: [
            new TableCell({ borders: allBorders, width: { size: 2400, type: WidthType.DXA }, shading: { fill: C.neutral, type: ShadingType.CLEAR }, margins: cellPad, columnSpan: 8,
              children: [p([t('SECONDARY CONTEXT — QCI5 (IMS signalling) and QCI9 (minor data)', { size: 18, bold: true, color: '888888' })])] })
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI5 — IMS (ms)', 2400, C.neutral), dataCell('RC3', 700),
            dataCell('17.98', 900), dataCell('17.71', 900), dataCell('17.89', 900),
            dataCell('−0.27 / −1.5%', 1100, C.neutral), dataCell('−1.7σ', 700),
            dataCell('Marginal (context only — 5.9% throughput share)', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI5 — IMS (ms)', 2400, C.neutral), dataCell('RC4', 700),
            dataCell('18.25', 900), dataCell('18.59', 900), dataCell('18.74', 900),
            dataCell('+0.34 / +1.9%', 1100, C.fail), dataCell('+4.9σ', 700),
            dataCell('Significant increase — driven by B2300_F1/F2 each +4.7%', 2480, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI9 (ms)', 2400, C.neutral), dataCell('RC3', 700),
            dataCell('32.96', 900), dataCell('34.10', 900), dataCell('34.59', 900),
            dataCell('+1.14 / +3.5%', 1100, C.warn), dataCell('+0.6σ', 700),
            dataCell('Directional (B700 +5.8%, B900 +6.9%) — context, low attempt volume', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('SDU Delay QCI9 (ms)', 2400, C.neutral), dataCell('RC4', 700),
            dataCell('32.71', 900), dataCell('34.00', 900), dataCell('34.76', 900),
            dataCell('+1.28 / +3.9%', 1100, C.warn), dataCell('+0.8σ', 700),
            dataCell('B700 +16.6% — likely confounded by RC4 B700 UL BLER anomaly', 2480, C.neutral)
          ]}),
          // --- overall ---
          new TableRow({ children: [
            dataCell('Avg Latency DL (ms) [feat. bands]', 2400, C.neutral), dataCell('RC3', 700),
            dataCell('86.3', 900), dataCell('84.7', 900), dataCell('85.7', 900),
            dataCell('−1.6ms / −1.8%', 1100, C.neutral), dataCell('−1.0σ', 700),
            dataCell('Within noise — consistent with QCI8 reduction', 2480, C.neutral)
          ]}),
          new TableRow({ children: [
            dataCell('Avg Latency DL (ms) [feat. bands]', 2400, C.neutral), dataCell('RC4', 700),
            dataCell('123.9', 900), dataCell('121.7', 900), dataCell('124.3', 900),
            dataCell('−2.3ms / −1.8%', 1100, C.neutral), dataCell('−0.9σ', 700),
            dataCell('Within noise; post-RB back to baseline level', 2480, C.neutral)
          ]}),
        ]
      }),
      spacer(),
      body('Neither focus bearer shows a latency improvement attributable to the feature. QCI8 delay (feature bands: 118ms RC3, 157ms RC4 baseline) reduced by 2–3ms — consistently across all four feature bands in both RCs, but well within daily variance at −0.6σ. A consistent directional reduction across eight independent per-carrier/per-RC observations is noted but cannot be declared statistically significant given the 7-day baseline. QCI1 VoLTE delay was essentially unchanged in both RCs, as expected — voice scheduling is GBR-prioritised and largely independent of TC muting. The RC4 QCI5 increase (+4.9σ) is driven by B2300 carriers (unaffected bands) and should not be attributed to CBXXXXXX.'),
      body('Verdict: PRIMARY OBJECTIVE NOT MET — no statistically significant latency improvement in QCI1 or QCI8 on the feature bands. The observed ~−1.8% directional reduction is consistent but within noise.', { bold: true }),
      spacer(),

      // ─── TIER 2 ────────────────────────────────────────────
      new Paragraph({ children: [new PageBreak()] }),
      h2('4.2 Tier 2 — Secondary KPIs'),

      h3('4.2.1 UL Residual BLER'),
      body('UL rBLER increased on feature bands in RC3 with statistical significance (+2.3σ). RC4 feature bands showed only a directional increase (+0.7σ — not significant). Critically, UL rBLER also increased on unaffected bands (RC3 +5.3%, +1.9σ; RC4 +28.1%, +6.1σ — the RC4 figure is dominated by a B700 outlier). The degradation on unaffected bands in both RCs indicates confounding interference or scheduling factors not related to CBXXXXXX, which partially weakens the attribution of the RC3 feature-band result.'),
      spacer(),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [1600, 700, 850, 850, 850, 850, 950, 1430],
        rows: [
          new TableRow({ children: [
            headerCell('UL rBLER (%)', 1600), headerCell('RC', 700),
            headerCell('B800 ▲', 850), headerCell('B900 ▲', 850), headerCell('B1800 ▲', 850),
            headerCell('B2100 ▲', 850), headerCell('Feat. Bands Avg', 950), headerCell('Sigma', 1430)
          ]}),
          new TableRow({ children: [
            dataCell('Baseline', 1600, C.neutral), dataCell('RC3', 700),
            dataCell('1.18', 850), dataCell('0.61', 850), dataCell('1.29', 850),
            dataCell('0.71', 850), dataCell('0.949', 950), dataCell('—', 1430)
          ]}),
          new TableRow({ children: [
            dataCell('Trial', 1600, C.warn), dataCell('RC3', 700),
            dataCell('1.27', 850, C.warn), dataCell('0.62', 850), dataCell('1.35', 850, C.warn),
            dataCell('0.73', 850), dataCell('0.993 (+4.7%)', 950, C.fail), dataCell('+2.3σ', 1430, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('Baseline', 1600, C.neutral), dataCell('RC4', 700),
            dataCell('1.58', 850), dataCell('1.08', 850), dataCell('1.54', 850),
            dataCell('0.89', 850), dataCell('1.274', 950), dataCell('—', 1430)
          ]}),
          new TableRow({ children: [
            dataCell('Trial', 1600, C.warn), dataCell('RC4', 700),
            dataCell('1.60', 850), dataCell('1.12', 850), dataCell('1.57', 850, C.warn),
            dataCell('0.90', 850), dataCell('1.297 (+1.8%)', 950, C.neutral), dataCell('+0.7σ', 1430, C.neutral)
          ]}),
          // separator
          new TableRow({ children: [
            new TableCell({ borders: allBorders, width: { size: 1600, type: WidthType.DXA }, shading: { fill: C.neutral, type: ShadingType.CLEAR }, margins: cellPad, columnSpan: 8,
              children: [p([t('UNAFFECTED BANDS impact check (B700 / B2300 — parameter unchanged)', { size: 16, italics: true, color: '888888' })])] })
          ]}),
          new TableRow({ children: [
            dataCell('Unaffected avg BL/Trial', 1600, C.neutral), dataCell('RC3', 700),
            new TableCell({ borders: allBorders, columnSpan: 4, width: { size: 3400, type: WidthType.DXA }, margins: cellPad, children: [p([t('B700+B2300 avg', { size: 16 })])] }),
            dataCell('0.693 → 0.730 (+5.3%)', 950, C.warn), dataCell('+1.9σ', 1430, C.warn)
          ]}),
          new TableRow({ children: [
            dataCell('Unaffected avg BL/Trial', 1600, C.neutral), dataCell('RC4', 700),
            new TableCell({ borders: allBorders, columnSpan: 4, width: { size: 3400, type: WidthType.DXA }, margins: cellPad, children: [p([t('B700 outlier (+49%) dominates — not feature related', { size: 16 })])] }),
            dataCell('0.856 → 1.097 (+28.1%)', 950, C.fail), dataCell('+6.1σ', 1430, C.fail)
          ]}),
        ]
      }),
      spacer(),
      body('▲ = Feature bands. RC3 shows a statistically significant UL rBLER degradation on feature bands (+2.3σ), with B800 and B1800 as the main contributors. RC4 feature bands are directional only (+0.7σ). The RC4 B700 anomaly (+49% rBLER, B700 is an UNAFFECTED band) is a separate issue specific to RC4 software; it recovered post-rollback.'),
      spacer(),
      body('UL MCS on feature bands declined in RC3 (−1.5%, n/a σ) and RC4 (−1.5%, −1.5σ). Lower UL MCS together with higher UL BLER is coherent: degraded UL link conditions. Given the parallel UL rBLER increase on unaffected bands, interference from neighbouring cells or UL scheduling changes should be investigated (RTWP data is available in the KPI export). The μDTX-without-TC mechanism may also alter the interference pattern seen by UL — but this cannot be isolated without a control cluster.'),
      spacer(),

      h3('4.2.2 DL BLER and Spectral Efficiency'),
      body('DL rBLER and DL initial BLER showed negligible changes in both RCs (all within ±0.3%, <1σ). DL Spectral Efficiency was essentially flat (RC3 +0.04%, RC4 −0.13%). The DL radio quality was unaffected. The degradation is UL-specific.'),
      spacer(),

      // ─── TIER 3 ─────────────────────────────────────────────
      h2('4.3 Tier 3 — Watchdog KPIs (Must Not Degrade)'),

      h3('4.3.1 E-RAB Retainability'),
      body('The E-RAB Retainability failure rate (RAN View — RNL Failure with UE Lost) is the most operationally impactful watchdog KPI, as it directly represents active session drops from the radio network side. Band-stratified analysis produces a nuanced picture:'),
      spacer(),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [1500, 700, 780, 780, 780, 780, 780, 950, 1050],
        rows: [
          new TableRow({ children: [
            headerCell('Retain. Fail (%)', 1500), headerCell('RC', 700),
            headerCell('B800▲', 780), headerCell('B900▲', 780), headerCell('B1800▲', 780),
            headerCell('B2100▲', 780), headerCell('B700●', 780),
            headerCell('Feat. Avg', 950), headerCell('Unaffect. Avg', 1050)
          ]}),
          new TableRow({ children: [
            dataCell('Baseline', 1500, C.neutral), dataCell('RC3', 700),
            dataCell('2.69', 780), dataCell('0.57', 780), dataCell('1.44', 780),
            dataCell('0.25', 780), dataCell('2.93', 780, C.neutral),
            dataCell('1.239', 950), dataCell('1.946', 1050)
          ]}),
          new TableRow({ children: [
            dataCell('Trial', 1500, C.warn), dataCell('RC3', 700),
            dataCell('3.55', 780, C.fail), dataCell('0.67', 780, C.warn), dataCell('1.63', 780, C.fail),
            dataCell('0.37', 780, C.warn), dataCell('3.75', 780, C.fail),
            dataCell('1.553 (+25.4%, +3.7σ)', 950, C.fail), dataCell('2.652 (+36.3%, +3.2σ)', 1050, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('Baseline', 1500, C.neutral), dataCell('RC4', 700),
            dataCell('4.92', 780), dataCell('1.64', 780), dataCell('1.70', 780),
            dataCell('0.45', 780), dataCell('7.26', 780, C.neutral),
            dataCell('2.178', 950), dataCell('3.709', 1050)
          ]}),
          new TableRow({ children: [
            dataCell('Trial', 1500, C.warn), dataCell('RC4', 700),
            dataCell('5.12', 780, C.warn), dataCell('1.74', 780, C.warn), dataCell('1.78', 780, C.warn),
            dataCell('0.47', 780), dataCell('9.75', 780, C.fail),
            dataCell('2.278 (+4.6%, +0.2σ)', 950, C.neutral), dataCell('4.895 (+32.0%, +3.2σ)', 1050, C.fail)
          ]}),
        ]
      }),
      spacer(),
      body('▲ = Feature bands (parameter changed). ● = Unaffected band (B700 shown; B2300_F1/F2 data similar in direction). The B2300 columns are omitted from this table for space but are included in the unaffected band average.', { italics: true, size: 16, color: '888888' }),
      spacer(),
      body('Key analytical observation: Retainability degraded on UNAFFECTED bands at comparable or higher magnitude than feature bands. In RC3, both feature bands (+3.7σ) and unaffected bands (+3.2σ) degraded significantly. In RC4, the feature-band average is NOT significant (+0.2σ), while unaffected bands degraded at +3.2σ — more severely than feature bands. This asymmetry is inconsistent with the feature being the sole driver.'),
      spacer(),
      body('Three competing hypotheses — all must be considered before attribution:'),
      bullet('H1 (Feature-induced): CBXXXXXX with TC=0 altered DL scheduling in a way that degraded UE connection stability on affected carriers. Supported by RC3 feature-band 3.7σ result.'),
      bullet('H2 (Concurrent network trend): A network-wide retainability degradation trend existed independently of the trial. Supported by significant degradation on unaffected bands in BOTH RCs, and by post-rollback continued deterioration (RC3 worsened to 2.329% post-rollback, not recovered).'),
      bullet('H3 (RC4 SW interaction): RC4 software version has stability issues on certain carriers independent of CBXXXXXX. Supported by RC4 B700 retainability crash (+34%) on an unaffected band.'),
      body('The most likely explanation is H1 + H2 in combination for RC3 (feature contribution on top of a background trend), and H2 + H3 for RC4 (feature-band retainability was marginal; unaffected-band degradation was more severe). A control cluster comparison is required to definitively isolate the feature contribution.'),
      spacer(),

      h3('4.3.2 E-RAB Drop Ratio'),
      body('Consistent directional worsening in both RCs, particularly on B700 and B800, but at lower statistical significance than retainability (RC3 +12.4% relative, +1.3σ; RC4 +9.9% relative, +1.0σ). The correlation with the retainability finding is directionally coherent, though these absolute magnitudes are at the borderline of noise given the short baseline.'),
      spacer(),

      h3('4.3.3 RC4 Accessibility — B2300_F1 and B2300_F2 (UNAFFECTED BANDS)'),
      body('The most alarming single finding in the dataset — and critically, it occurred on carriers where allowTrafficConcentration was NOT changed (B2300_F1 and B2300_F2 remained at TC=1 throughout). During the trial period, B2300_F1 and B2300_F2 in RC4 experienced severe accessibility degradation:'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2500, 1200, 1200, 1200, 1200, 2780],
        rows: [
          new TableRow({ children: [
            headerCell('Metric', 2500), headerCell('Carrier', 1200),
            headerCell('Baseline', 1200), headerCell('Trial', 1200),
            headerCell('Post-RB', 1200), headerCell('Comment', 2780)
          ]}),
          new TableRow({ children: [
            dataCell('RRC SR (%)', 2500, C.neutral), dataCell('B2300_F1', 1200),
            dataCell('99.980', 1200, C.pass), dataCell('98.649', 1200, C.fail), dataCell('98.282', 1200, C.fail),
            dataCell('−1.33pp; failure rate ×5', 2780, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('RRC SR (%)', 2500, C.neutral), dataCell('B2300_F2', 1200),
            dataCell('99.970', 1200, C.pass), dataCell('98.019', 1200, C.fail), dataCell('97.886', 1200, C.fail),
            dataCell('−1.95pp; failure rate ×9', 2780, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('Initial E-RAB Accessibility (%)', 2500, C.neutral), dataCell('B2300_F1', 1200),
            dataCell('99.883', 1200, C.pass), dataCell('98.442', 1200, C.fail), dataCell('98.098', 1200, C.fail),
            dataCell('−1.44pp; failure rate tripled', 2780, C.fail)
          ]}),
          new TableRow({ children: [
            dataCell('Initial E-RAB Accessibility (%)', 2500, C.neutral), dataCell('B2300_F2', 1200),
            dataCell('99.859', 1200, C.pass), dataCell('97.824', 1200, C.fail), dataCell('97.506', 1200, C.fail),
            dataCell('−2.03pp; failure rate ×5', 2780, C.fail)
          ]}),
        ]
      }),
      spacer(),
      body('This degradation is not observed in RC3 for the same carriers. Since B2300 was in the UNAFFECTED band group (TC remained enabled throughout), this crash CANNOT be attributed to the CBXXXXXX parameter change. It is an RC4 software-version-specific instability — possibly triggered by a software interaction during the trial period window regardless of the CBXXXXXX activation, or a concurrent carrier-specific configuration issue. The continued degradation post-rollback confirms the rollback of CBXXXXXX alone did not resolve it. A Nokia vendor case is required for RC4/B2300 specifically, independent of the trial verdict.'),
      spacer(),

      h3('4.3.4 RC4 Intra-eNB Handover'),
      body('RC4 feature-band aggregate HO intra-eNB: −0.81% (−3.2σ) — statistically significant but small absolute delta. Carrier detail: B1800 (feature band) dropped from 98.35% to 96.09% (−2.26pp) — a large customer-impacting degradation. B700 (UNAFFECTED band) dropped from 99.02% to 96.21% (−2.81pp). The B700 degradation on an unaffected band confirms this is an RC4 software-version issue extending beyond the CBXXXXXX parameter scope. Neither B1800 nor B700 showed similar degradation in RC3, pointing to an RC4-specific interaction.'),
      spacer(),

      h3('4.3.5 Accessibility — Feature Bands vs Unaffected (RC3/RC4)'),
      body('RC3 feature bands: all accessibility KPIs within noise (<0.1pp). Unaffected bands (RC3): also broadly stable. RC4 feature bands: RRC SR −0.07% (−3.8σ statistically but tiny absolute — baseline near-zero variance inflating sigma), E-RAB SR essentially flat. RC4 unaffected bands: severe degradation driven by B2300 crash (RRC SR −1.13%, −61.7σ; Initial E-RAB −1.25%, −58.5σ — these extremely high sigma values reflect near-zero baseline variance on those KPIs; the absolute degradations of −1.1pp and −1.25pp are the operationally meaningful figure). RC4 RACH SR on unaffected bands: −0.43% (−4.6σ).'),
      spacer(),

      h3('4.3.6 Cell Availability'),
      body('Feature bands: RC3 −0.27% (−0.3σ) — stable. RC4 −0.03% — stable. Unaffected bands: RC3 −1.26% (−3.8σ) — significant on unaffected bands. The RC3 unaffected-band cell availability drop is notable but not reflected in feature bands. This is another indicator of a confounding network event affecting B700/B2300 during the trial period independently of CBXXXXXX.'),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 5. CONFOUNDERS
      // ═══════════════════════════════════════════════════════
      new Paragraph({ children: [new PageBreak()] }),
      h1('5. Confounding Factor Assessment'),

      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2800, 2400, 4880],
        rows: [
          new TableRow({ children: [headerCell('Factor', 2800), headerCell('Status', 2400), headerCell('Notes', 4880)] }),
          new TableRow({ children: [
            dataCell('Traffic load increase', 2800), dataCell('Excluded', 2400, C.pass),
            dataCell('PRB utilisation and connected UEs stable; RC4 traffic slightly lighter during trial', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Hardware failure', 2800), dataCell('Unlikely — not confirmed', 2400, C.warn),
            dataCell('Cross-RC consistency argues against a single hardware event. B2300 RC4 crash not mirrored in RC3. No alarm data available.', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Software upgrade (beyond RC versioning)', 2800), dataCell('Unknown', 2400, C.warn),
            dataCell('No information provided. Cannot be excluded. However, if an SW upgrade caused the degradation, it would more likely affect both RCs similarly.', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Seasonal / propagation', 2800), dataCell('Low risk', 2400, C.pass),
            dataCell('Jan–Mar window, sub-6GHz bands, urban morphology assumed. Foliage effects minimal in winter. No unusual weather events indicated.', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Neighbour network changes', 2800), dataCell('Unknown', 2400, C.warn),
            dataCell('New cell activations or power changes on adjacent carriers could explain UL BLER increase. RTWP data (available) should be checked for interference increase.', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Pre-existing retainability trend', 2800), dataCell('LIKELY — supported by data', 2400, C.warn),
            dataCell('Band-stratified analysis shows retainability degradation on UNAFFECTED bands (B700, B2300) in both RCs at comparable or greater magnitude than feature bands. RC4 feature-band retainability was not significant (+0.2σ) while unaffected bands degraded at +3.2σ. Post-rollback retainability continued to deteriorate. Together these strongly suggest a concurrent network-wide degradation trend. A control cluster is required to isolate the feature contribution.', 4880)
          ]}),
          new TableRow({ children: [
            dataCell('Short baseline (7 days)', 2800), dataCell('Confirmed limitation', 2400, C.fail),
            dataCell('Sigma calculations are unreliable at N=7. This most affects results in the 1–3σ range. Results above 3.4σ (UL BLER RC3, retainability RC3, accessibility RC4) remain credible even with baseline uncertainty.', 4880)
          ]}),
        ]
      }),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 6. CONCLUSION AND RECOMMENDATION
      // ═══════════════════════════════════════════════════════
      h1('6. Conclusion and Recommendation'),

      h2('6.1 Verdict'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [2000, 8080],
        rows: [
          new TableRow({ children: [
            headerCell('VERDICT', 2000),
            new TableCell({
              borders: allBorders, width: { size: 8080, type: WidthType.DXA },
              shading: { fill: C.fail, type: ShadingType.CLEAR }, margins: cellPad,
              children: [p([t('FAIL — Rollback was the correct action. Feature CBXXXXXX with allowTrafficConcentration = 0 must not be deployed network-wide.', { size: 22, bold: true, color: C.red })])]
            })
          ]}),
          new TableRow({ children: [
            headerCell('REASONING', 2000),
            new TableCell({
              borders: allBorders, width: { size: 8080, type: WidthType.DXA },
              shading: { fill: C.neutral, type: ShadingType.CLEAR }, margins: cellPad,
              children: [
                p([t('1. Primary objective (power saving) — FEATURE BANDS: no statistically meaningful improvement. PSM +1.9%, ReducedTX +2.3% — directional but sub-1σ in all cases.', { size: 20 })]),
                p([t('2. Primary objective (latency) — FEATURE BANDS: ~−1.8% reduction in DL latency and QCI8 delay, consistent across all 4 bands in both RCs, but −0.6σ to −1.0σ — within noise. No definitive latency improvement can be claimed.', { size: 20 })]),
                p([t('3. UL BLER — FEATURE BANDS: RC3 significant (+4.7%, +2.3σ); RC4 directional only (+1.8%, +0.7σ). Cross-RC inconsistency. Parallel degradation on unaffected bands indicates a confounding interference factor.', { size: 20 })]),
                p([t('4. E-RAB Retainability — FEATURE BANDS: RC3 significant (+25.4%, +3.7σ). RC4 not significant (+4.6%, +0.2σ). Unaffected bands degraded at equal or greater magnitude in both RCs — strong indication of a concurrent network trend. Attribution to CBXXXXXX is partial, not exclusive.', { size: 20 })]),
                p([t('5. RC4 B2300 accessibility crash (UNAFFECTED BAND — TC was NOT changed): failure rate 5–9× on B2300_F1/F2. This is an RC4 software-version-specific issue, NOT caused by the CBXXXXXX parameter. Requires a Nokia vendor case.', { size: 20 })]),
                p([t('6. RC3 is the stronger evidence base for any feature contribution (UL rBLER 2.3σ, retainability 3.7σ on feature bands). RC4 feature bands were broadly within noise; RC4 unaffected bands show more severe watchdog degradation, indicating an RC4 SW stability problem.', { size: 20 })]),
              ]
            })
          ]}),
        ]
      }),
      spacer(),

      h2('6.2 Immediate Actions'),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Confirm allowTrafficConcentration = 1 is active on all trial sites in both RC3 and RC4.', { size: 20 })] }),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Raise a Nokia vendor case for the B2300_F1/F2 accessibility crash in RC4 — the non-recovery post-rollback indicates a potential software defect or parameter lock requiring vendor-side resolution.', { size: 20, color: C.red, bold: true })] }),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Monitor E-RAB Retainability on all trial sites weekly for at least 4 weeks post-rollback to confirm whether the deterioration trend is trial-related or ongoing.', { size: 20 })] }),
      new Paragraph({ numbering: { reference: 'numbers', level: 0 }, children: [t('Check RTWP data on B700 and B800 (available in the KPI export, not analyzed here) to determine whether UL BLER degradation correlates with wideband interference increase.', { size: 20 })] }),
      spacer(),

      h2('6.3 If Re-Trial is Considered'),
      body('If Nokia or the network team proposes a re-trial of this feature, the following conditions should be required:'),
      bullet('Minimum 4-week baseline period before any parameter change'),
      bullet('Control cluster of equal size and traffic profile, with no parameter changes, running in parallel to allow confounder isolation'),
      bullet('Resolve the RC4/B2300 SW defect before re-activating the feature'),
      bullet('Daily monitoring of UL BLER and E-RAB Retainability during the trial with predefined abort thresholds (e.g., rollback if cluster retainability failure rate exceeds baseline by >10% for 3 consecutive days)'),
      bullet('UL Latency data must be included in the KPI export — the absence of this metric in the current export is a data gap against the trial objective'),
      spacer(),

      // ═══════════════════════════════════════════════════════
      // 7. APPENDIX
      // ═══════════════════════════════════════════════════════
      new Paragraph({ children: [new PageBreak()] }),
      h1('7. Appendix — Summary Statistics'),

      body('Tables show feature-band aggregate values (B800 + B900 + B1800 + B2100) for all KPIs. Selected unaffected-band (B700 / B2300) impact-check rows are included at the bottom of each table, prefixed [UNAFFECTED].', { italics: true }),
      spacer(),
      h2('7.1 Complete KPI Table — RC3 (Feature Bands ▲)'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [3200, 1000, 1000, 1000, 1080, 680, 1120],
        rows: [
          new TableRow({ children: [
            headerCell('KPI', 3200), headerCell('Baseline', 1000), headerCell('Trial', 1000),
            headerCell('Post-RB', 1000), headerCell('Delta', 1080), headerCell('Sigma', 680), headerCell('Tier', 1120)
          ]}),
          ...[
            ['PSM Ratio (%) ▲', '15.20', '15.49', '15.81', '+0.29 / +1.9%', '+0.5σ', 'T1', false],
            ['DRX Sleep Ratio (%) ▲', '63.85', '63.80', '64.38', '−0.05 / −0.1%', '−0.2σ', 'T1', false],
            ['Avg Latency DL (ms) ▲', '86.3', '84.7', '85.7', '−1.6 / −1.8%', '−1.0σ', 'T1', false],
            ['SDU Delay QCI1 VoLTE ★▲ (ms)', '11.00', '10.97', '11.00', '−0.03 / −0.3%', '−0.2σ', 'T1', false],
            ['SDU Delay QCI8 primary ★▲ (ms)', '118.0', '115.9', '117.0', '−2.1 / −1.7%', '−0.6σ', 'T1', false],
            ['SDU Delay QCI5 IMS (ms)', '16.93', '16.40', '16.48', '−0.53 / −3.1%', '−1.9σ', 'T1 ctx', false],
            ['SDU Delay QCI9 (ms)', '32.46', '33.14', '33.65', '+0.68 / +2.1%', '+0.3σ', 'T1 ctx', false],
            ['UL rBLER (%) ▲', '0.949', '0.993', '1.017', '+0.044 / +4.7%', '+2.3σ', 'T2', true],
            ['DL rBLER (%) ▲', '0.022', '0.022', '0.022', '+0.000 / +1.2%', '+0.3σ', 'T2', false],
            ['Avg UL MCS ▲', '10.25', '10.10', '10.00', '−0.15 / −1.5%', 'n/a', 'T2', false],
            ['Tput DL Active (kbps) ▲', '10671', '10503', '10462', '−168 / −1.6%', '−0.4σ', 'T2', false],
            ['Tput UL Active (kbps) ▲', '1838', '1801', '1823', '−37 / −2.0%', '−0.4σ', 'T2', false],
            ['PRB Util DL (%) ▲', '19.81', '19.52', '19.83', '−0.29 / −1.5%', '−0.7σ', 'CTX', false],
            ['Cell Availability (%) ▲', '84.16', '83.93', '83.44', '−0.23 / −0.3%', '−0.3σ', 'T3', false],
            ['RACH SR (%) ▲', '97.69', '97.89', '97.82', '+0.20 / +0.2%', '+0.9σ', 'T3', false],
            ['E-RAB SR (%) ▲', '99.788', '99.783', '99.799', '−0.005 / 0.0%', '−0.3σ', 'T3', false],
            ['RRC SR (%) ▲', '99.756', '99.729', '99.739', '−0.027 / 0.0%', '−1.2σ', 'T3', false],
            ['E-RAB Drop Ratio (%) ▲', '0.434', '0.494', '0.527', '+0.060 / +13.8%', '+1.4σ', 'T3', true],
            ['ERAB Retainability Fail (%) ▲', '1.239', '1.553', '2.329', '+0.314 / +25.4%', '+3.7σ', 'T3', true],
            ['HO Intra-eNB SR (%) ▲', '99.176', '99.116', '99.119', '−0.060 / −0.1%', '−0.9σ', 'T3', false],
            ['[UNAFFECTED] Retainability Fail ●', '1.946', '2.652', '3.147', '+0.706 / +36.3%', '+3.2σ', 'IMPACT', true],
            ['[UNAFFECTED] Cell Availability ●', '87.99', '86.88', '88.92', '−1.11 / −1.3%', '−3.8σ', 'IMPACT', true],
          ].map(([kpi, b, tr, pr, delta, sig, tier, bad]) => new TableRow({
            children: [
              dataCell(kpi, 3200, C.neutral),
              dataCell(b, 1000, null, false, '000000', AlignmentType.CENTER),
              dataCell(tr, 1000, bad ? C.fail : null, false, '000000', AlignmentType.CENTER),
              dataCell(pr, 1000, null, false, '000000', AlignmentType.CENTER),
              dataCell(delta, 1080, bad ? C.fail : null, bad, bad ? C.red : '000000', AlignmentType.CENTER),
              dataCell(sig, 680, null, false, '000000', AlignmentType.CENTER),
              dataCell(tier, 1120, null, false, '888888', AlignmentType.CENTER),
            ]
          }))
        ]
      }),
      spacer(),

      h2('7.2 Complete KPI Table — RC4 (Feature Bands ▲)'),
      new Table({
        width: { size: 10080, type: WidthType.DXA },
        columnWidths: [3200, 1000, 1000, 1000, 1080, 680, 1120],
        rows: [
          new TableRow({ children: [
            headerCell('KPI', 3200), headerCell('Baseline', 1000), headerCell('Trial', 1000),
            headerCell('Post-RB', 1000), headerCell('Delta', 1080), headerCell('Sigma', 680), headerCell('Tier', 1120)
          ]}),
          ...[
            ['PSM Ratio (%) ▲', '14.21', '14.29', '13.99', '+0.08 / +0.6%', '+0.1σ', 'T1', false],
            ['DRX Sleep Ratio (%) ▲', '65.43', '65.71', '66.32', '+0.28 / +0.4%', '+1.8σ', 'T1', false],
            ['Avg Latency DL (ms) ▲', '123.9', '121.7', '124.3', '−2.3 / −1.8%', '−0.9σ', 'T1', false],
            ['SDU Delay QCI1 VoLTE ★▲ (ms)', '11.18', '11.21', '11.25', '+0.03 / +0.3%', '+0.2σ', 'T1', false],
            ['SDU Delay QCI8 primary ★▲ (ms)', '157.0', '153.9', '156.4', '−3.1 / −2.0%', '−0.6σ', 'T1', false],
            ['SDU Delay QCI5 IMS (ms)', '17.50', '17.49', '17.69', '−0.01 / 0.0%', 'n/a', 'T1 ctx', false],
            ['SDU Delay QCI9 (ms)', '36.18', '36.86', '37.62', '+0.68 / +1.9%', '+0.4σ', 'T1 ctx', false],
            ['UL rBLER (%) ▲', '1.274', '1.297', '1.318', '+0.023 / +1.8%', '+0.7σ', 'T2', false],
            ['DL rBLER (%) ▲', '0.026', '0.025', '0.025', '−0.001 / −1.0%', '−0.1σ', 'T2', false],
            ['Avg UL MCS ▲', '9.21', '9.07', '8.98', '−0.14 / −1.5%', '−1.5σ', 'T2', false],
            ['Tput DL Active (kbps) ▲', '9628', '9669', '9711', '+41 / +0.4%', '+0.1σ', 'T2', false],
            ['Tput UL Active (kbps) ▲', '1376', '1383', '1414', '+7 / +0.5%', '+0.2σ', 'T2', false],
            ['PRB Util DL (%) ▲', '23.84', '23.58', '24.18', '−0.26 / −1.1%', '−0.3σ', 'CTX', false],
            ['Cell Availability (%) ▲', '85.14', '85.11', '85.45', '−0.03 / 0.0%', '−0.0σ', 'T3', false],
            ['RACH SR (%) ▲', '98.717', '98.642', '98.565', '−0.075 / −0.1%', '−0.5σ', 'T3', false],
            ['E-RAB SR (%) ▲', '99.756', '99.754', '99.722', '−0.002 / 0.0%', '−0.1σ', 'T3', false],
            ['RRC SR (%) ▲', '99.729', '99.660', '99.637', '−0.069 / −0.1%', '−3.8σ', 'T3', true],
            ['E-RAB Drop Ratio (%) ▲', '0.435', '0.438', '0.513', '+0.003 / +0.7%', '+0.1σ', 'T3', false],
            ['ERAB Retainability Fail (%) ▲', '2.178', '2.278', '2.516', '+0.100 / +4.6%', '+0.2σ', 'T3', false],
            ['HO Intra-eNB SR (%) ▲', '97.151', '96.366', '96.271', '−0.785 / −0.8%', '−3.2σ', 'T3', true],
            ['[UNAFFECTED] Retainability Fail ●', '3.709', '4.895', '3.843', '+1.186 / +32.0%', '+3.2σ', 'IMPACT', true],
            ['[UNAFFECTED] RRC SR ● (B2300 crash)', '99.917', '98.784', '98.646', '−1.133 / −1.1%', '−61.7σ', 'IMPACT', true],
            ['[UNAFFECTED] HO Intra ● (B700)', '99.396', '98.458', '99.068', '−0.938 / −0.9%', '−3.7σ', 'IMPACT', true],
          ].map(([kpi, b, tr, pr, delta, sig, tier, bad]) => new TableRow({
            children: [
              dataCell(kpi, 3200, C.neutral),
              dataCell(b, 1000, null, false, '000000', AlignmentType.CENTER),
              dataCell(tr, 1000, bad ? C.fail : null, false, '000000', AlignmentType.CENTER),
              dataCell(pr, 1000, null, false, '000000', AlignmentType.CENTER),
              dataCell(delta, 1080, bad ? C.fail : null, bad, bad ? C.red : '000000', AlignmentType.CENTER),
              dataCell(sig, 680, null, false, '000000', AlignmentType.CENTER),
              dataCell(tier, 1120, null, false, '888888', AlignmentType.CENTER),
            ]
          }))
        ]
      }),
      spacer(),

      body('Legend: T1 = Tier 1 Primary KPI | T1 ctx = Tier 1 context-only (secondary QCI) | T2 = Tier 2 Secondary KPI | T3 = Tier 3 Watchdog KPI | CTX = Context/Load indicator | IMPACT = Unaffected-band impact check row', { italics: true, size: 16, color: '888888' }),
      body('▲ = Feature bands (B800/B900/B1800/B2100) — where allowTrafficConcentration was changed to 0. Primary analysis scope.', { italics: true, size: 16, color: '888888' }),
      body('● = Unaffected bands (B700/B2300_F1/B2300_F2) — parameter was NOT changed. Degradation on these rows indicates confounders, not feature effects.', { italics: true, size: 16, color: '888888' }),
      body('★ = Primary bearer KPIs for latency analysis: QCI1 (VoLTE) and QCI8 (dominant data bearer — 2.28B E-RAB attempts, 54.3% DL throughput share).', { italics: true, size: 16, color: '888888' }),
      body('Red shading = degradation considered operationally material. Sigma based on 7-day baseline — treat 1–3σ results as directional. Very high sigma values (>10σ) on near-zero-variance KPIs (e.g. RRC SR) reflect statistical artefact; the absolute pp delta is the operative metric.', { italics: true, size: 16, color: '888888' }),

    ]
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync('CBXXXXXX_Trial_Analysis.docx', buf);
  console.log('Done.');
});
