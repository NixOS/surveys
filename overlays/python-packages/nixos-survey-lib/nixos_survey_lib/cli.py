"""nixos-survey-limesurvey: convert a survey.toml into LimeSurvey's import file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .limesurvey import to_tsv
from .schema import SurveyError, load_survey


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code: 0 on success, 1 when the
    survey definition fails to load (the message goes to stderr)."""
    parser = argparse.ArgumentParser(
        prog="nixos-survey-limesurvey",
        description="Write the LimeSurvey tab-separated survey structure for a survey.toml. "
        "Text files (survey.<lang>.toml) are read from the same directory.",
    )
    parser.add_argument("structure", type=Path, help="path to survey.toml")
    parser.add_argument("-o", "--output", type=Path, help="write here instead of stdout")
    args = parser.parse_args(argv)

    try:
        survey = load_survey(args.structure)
    except SurveyError as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    tsv = to_tsv(survey)
    if args.output is None:
        # Bytes, not text: keeps the BOM and newlines exact regardless of locale.
        sys.stdout.buffer.write(tsv.encode("utf-8"))
    else:
        with args.output.open("w", encoding="utf-8", newline="") as f:
            f.write(tsv)
    return 0


if __name__ == "__main__":
    sys.exit(main())
