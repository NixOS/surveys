# community/2025/generate_dummy.py
"""Generate a synthetic responses CSV for the 2025 community survey.

Writes:
  argv[1] — path to write the synthetic CSV to

Everything is fabricated from survey.toml with a fixed seed; no real
survey rows are involved. Pool contents come from public Nix release
history and the answer formats the pipeline's normalizers handle
(extract_first_semver, normalize_yes_no) — only the charted text
questions need plausible variety, every other text question just needs
a column to exist.
"""

import sys
from pathlib import Path

from nixos_survey_lib.schema import load_survey
from nixos_survey_lib.synthesize import synthesize_csv

TEXT_POOLS = {
    # Charted via extract_first_semver: bare semvers, command-output
    # style, and junk, so the version chart gets real buckets plus
    # nonzero "No Match" and "Skipped".
    "nixVersion": [
        "2.3.16",
        "2.18.1",
        "2.18.9",
        "2.24.3",
        "2.24.9",
        "2.25.2",
        "2.28.0",
        "nix (Nix) 2.24.3",
        "nix (Nix) 2.18.1",
        "Lix 2.91.0",
        "whatever nixpkgs unstable ships",
        "I don't know",
    ],
    # Charted via normalize_yes_no: recognized aliases plus free-form
    # strings that land in the "Other" bucket.
    "workplaceUsesNix": [
        "Yes",
        "yes",
        "yep",
        "No",
        "no",
        "nope",
        "Only on my team's CI",
    ],
    "workplaceDecision": [
        "Yes",
        "y",
        "No",
        "n",
        "nah",
        "It was decided before I joined",
    ],
}


def main(out_path: str) -> None:
    here = Path(__file__).resolve().parent
    schema = load_survey(here / "survey.toml")
    # 1000 rows keeps crosstab cells (sankey/heatmap) above min-count
    # suppression even for low-weight choices crossed with many categories.
    synthesize_csv(schema, Path(out_path), rows=1000, text_pools=TEXT_POOLS)


if __name__ == "__main__":
    main(sys.argv[1])
