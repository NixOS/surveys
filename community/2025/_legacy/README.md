# Legacy 2025 processing code

This directory preserves the previous Panel/Altair/Vega pipeline for
parity-checking against the new `nixos-survey-lib`-based pipeline.

Once the new pipeline has produced one published artifact and parity is
confirmed (Task 8 of plan 3), this directory will be removed in a separate
PR.

Files:
- `altplot.py` — old chart construction helpers
- `process.py` — old top-level composition
- `dfhelpers.py` — old polars/pandas utility helpers
- `export.py` — HTML/PDF export driver
