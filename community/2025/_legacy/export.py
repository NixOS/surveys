"""Export the survey dashboard to a standalone HTML file and (optionally) PDF.

Usage:
    python export.py                          # write nix-community-survey-2025.html
    python export.py --pdf                    # also write the PDF
    python export.py --output-dir build/      # custom output directory
    python export.py --html-only --out my.html
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def find_chromium() -> str | None:
    for name in ("chromium", "chrome", "google-chrome", "google-chrome-stable"):
        path = shutil.which(name)
        if path:
            return path
    return None


def render_pdf(html_path: Path, pdf_path: Path, window_size: str = "1600,2400") -> None:
    chromium = find_chromium()
    if chromium is None:
        raise RuntimeError(
            "Could not find chromium/chrome on PATH. Install one of: "
            "chromium, chrome, google-chrome, google-chrome-stable."
        )
    cmd = [
        chromium,
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        f"--window-size={window_size}",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}",
        f"file://{html_path.resolve()}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"chromium exited with code {result.returncode}:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export the survey dashboard to HTML (and optionally PDF)."
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write outputs into (default: current directory).",
    )
    parser.add_argument(
        "--out",
        default="nix-community-survey-2025.html",
        help="HTML filename (default: nix-community-survey-2025.html).",
    )
    parser.add_argument(
        "--pdf",
        action="store_true",
        help="Also render a PDF via headless chromium.",
    )
    parser.add_argument(
        "--html-only",
        action="store_true",
        help="Skip PDF even if --pdf was passed elsewhere (no-op unless used).",
    )
    parser.add_argument(
        "--window-size",
        default="1600,2400",
        help="Headless chromium window size for PDF rendering (default 1600,2400).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    html_path = out_dir / args.out
    pdf_path = html_path.with_suffix(".pdf")

    # Import process here so the dashboard builds with its own working directory
    # (process.py reads the CSV relative to its file location).
    here = Path(__file__).resolve().parent
    if str(here) not in sys.path:
        sys.path.insert(0, str(here))
    import process

    print(f"Saving HTML to {html_path} ...")
    process.app.save(str(html_path), resources="inline")
    print(f"Wrote {html_path} ({html_path.stat().st_size // 1024} KiB)")

    if args.pdf and not args.html_only:
        print(f"Rendering PDF to {pdf_path} ...")
        render_pdf(html_path, pdf_path, window_size=args.window_size)
        print(f"Wrote {pdf_path} ({pdf_path.stat().st_size // 1024} KiB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
