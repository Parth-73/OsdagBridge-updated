# Report generator verification

The 50-page A4 report in [Report_After.pdf](reports/Report_After.pdf) uses the same 20 m, four-girder Mumbai sample as Report_Final.pdf. The structural solver, formulas and acceptance criteria are unchanged.

| Files changed | Reason and implementation |
|---|---|
| core/reports/chap2.py | Replaced six narrow compound columns with girder, parameter and value rows. Girder identity is present even across page breaks. Dimension headers use two lines and right-aligned values. |
| core/bridge_types/plate_girder/analyser.py and plategirderbridge.py | Capture the magnitudes already assigned to the steel load lines and wet-concrete patch in the analysis snapshot. The material dialog density inputs previously appeared under applied-load labels. |
| core/reports/chap3.py and report_generator.py | Pass the snapshot into Chapter 3 and report each applied line load with its transverse coordinate, the slab pressure, and separately labeled material inputs. Older snapshots display Not reported. |
| core/bridge_types/plate_girder/designer.py and core/reports/chap5.py | Preserve the checked spacing used by each girder's intermediate-stiffener calculation. Guidance-only results identify a required minimum. The legacy shared spacing belongs only to the identified controlling girder. Include each girder's normal fatigue check alongside the component overview charts. |
| tests/unit/test_reports.py | Add regressions for applied-load units, zero and missing values, different spacing availability per girder and preservation of multiple fatigue ratios in chart data. |

Source paths in the table start at src/osdagbridge unless otherwise indicated.

## Verification

The full suite passed (28 tests) with one third-party pytest deprecation warning. Existing tests cover repeating headings, critical failures, live-load separation, chart thresholds and quantities, and PDF compilation. All three pdfLaTeX passes succeeded. The final log contained no overfull boxes. Rendered all 50 pages and reviewed page layouts, continuation headers, charts and footer clearance. The revised geometry tables are on pages 9–10, applied loads on page 13, stiffener results on pages 30–31, utilization charts on pages 42–43 and material charts on pages 45–46.

The unit-weight inputs are absent in this sample. Recorded applied loads are 1.224 kN/m on each of four lines and 6.25 kN/m² on the deck. All four stiffener checks used 1635 mm. Girder fatigue ratios are 2.31, 2.49, 2.60 and 2.61, and G4 governs the overall FAIL. The 44 m/s site versus 33 m/s analysis warning remains.

The six presentation requirements are met for this sample. The existing styles.py, tables.py and charts.py continue to control shared typography, page geometry, continuation headers and chart styling. Column widths specific to individual tables remain in their chapters. The drawing chapter reports unavailable CAD views. An end-diaphragm capacity result was unavailable in the sample.
