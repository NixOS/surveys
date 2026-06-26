inputs:

let
  inherit (inputs.nixpkgs-lib.lib.attrsets) mapAttrs;
in
mapAttrs (system: pkgs: {
  default = pkgs.mkShell {
    packages = [
      (pkgs.python3.withPackages (ps: [ ps.polars ps.pyyaml ps.pytest ]))
      pkgs.nodejs_22
      pkgs.watchexec
    ];

    shellHook = ''
      export PYTHONPATH=$PWD/overlays/python-packages/nixos-survey-lib:$PYTHONPATH

      # `dev` serves the site. Default: use the committed vendored JSON (no CSV
      # needed, no pipeline watching — Astro still HMRs all component/CSS/client
      # edits). `dev --live`: recompute from the CSV (requires the CSV in the
      # Nix store) and watchexec-rebuild on pipeline changes, as before.
      dev() (
        if [ ! -d "lib/site" ]; then
          echo "[dev] must be run from the surveys repo root" >&2
          return 1
        fi

        target="lib/site/src/content/results/results-2025.json"
        vendored="overlays/top-level/nixos-surveys-community-2025-data/results-2025.json"
        mkdir -p "$(dirname "$target")"

        if [ "$1" = "--live" ]; then
          data_drv=".#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data-from-csv"
          echo "[dev] live mode: building data from CSV..."
          if ! out=$(nix build --no-link --print-out-paths "$data_drv"); then
            echo "[dev] data build failed." >&2
            echo "      If the survey CSV is missing from /nix/store, add it:" >&2
            echo "      nix-store --add-fixed sha256 <path-to-CSV>" >&2
            return 1
          fi
          install -m 0644 "$out/results-2025.json" "$target"
          echo "[dev] data ready (live) at $target"

          watchexec -e py,md,yaml -w community/2025 -w overlays/python-packages/nixos-survey-lib --postpone -- bash -c '
            out=$(nix build --no-link --print-out-paths .#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data-from-csv) \
              && install -m 0644 "$out/results-2025.json" lib/site/src/content/results/results-2025.json \
              && echo "[dev] data updated"
          ' &
          watch_pid=$!
          trap 'kill $watch_pid 2>/dev/null' INT TERM EXIT
        else
          echo "[dev] vendored mode: using committed data (run 'dev --live' to recompute from CSV)"
          install -m 0644 "$vendored" "$target"
          echo "[dev] data ready (vendored) at $target"
        fi

        # Reinstall when node_modules is missing, or when the lockfile is newer
        # than the last install (npm refreshes node_modules/.package-lock.json on
        # every install) — so dependency changes aren't silently skipped.
        if [ ! -d lib/site/node_modules ] || [ lib/site/package-lock.json -nt lib/site/node_modules/.package-lock.json ]; then
          echo "[dev] installing npm dependencies..."
          (cd lib/site && npm install --silent)
        fi
        (cd lib/site && npm run dev)
      )

      # Regenerate the committed vendored JSON from the raw CSV (requires the CSV
      # in the Nix store). Run after pipeline/commentary changes, then commit the
      # updated file.
      vendor-data() (
        if [ ! -d "lib/site" ]; then
          echo "[vendor-data] must be run from the surveys repo root" >&2
          return 1
        fi
        vendored="overlays/top-level/nixos-surveys-community-2025-data/results-2025.json"
        echo "[vendor-data] building data from CSV..."
        if ! out=$(nix build --no-link --print-out-paths .#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data-from-csv); then
          echo "[vendor-data] build failed; is the CSV in the Nix store?" >&2
          echo "      nix-store --add-fixed sha256 <path-to-CSV>" >&2
          return 1
        fi
        install -m 0644 "$out/results-2025.json" "$vendored"
        echo "[vendor-data] wrote $vendored — review and commit it."
      )

      echo "Surveys dev shell."
      echo ""
      echo "Live dev (vendored data):  dev"
      echo "Live dev (recompute CSV):  dev --live"
      echo "Regenerate vendored JSON:  vendor-data"
      echo "Run tests:                 pytest overlays/python-packages/nixos-survey-lib/tests/"
    '';
  };
}) inputs.self.legacyPackages
