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

      # `dev` runs the live pipeline in one terminal:
      #   - builds the nixos-surveys-community-2025-data derivation (which uses
      #     the requireFile'd CSV from /nix/store, so the raw CSV need NOT live
      #     in the working tree)
      #   - watchexec rebuilds it on .py changes
      #   - Astro dev server serves with HMR; the JSON copy lands in its content
      #     collection so HMR refreshes the page automatically
      # Ctrl-C in the Astro foreground cleanly tears watchexec down via EXIT trap.
      dev() (
        if [ ! -d "lib/site" ]; then
          echo "[dev] must be run from the surveys repo root" >&2
          return 1
        fi

        data_drv=".#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data"
        target="lib/site/src/content/results/results-2025.json"

        echo "[dev] building data derivation..."
        if ! out=$(nix build --no-link --print-out-paths "$data_drv"); then
          echo "[dev] initial data build failed." >&2
          echo "      If the survey CSV is missing from /nix/store, add it:" >&2
          echo "      nix-store --add-fixed sha256 <path-to-CSV>" >&2
          return 1
        fi
        mkdir -p "$(dirname "$target")"
        # install (not cp) so the target stays writable — the source lives in the
        # read-only /nix/store, and a plain cp onto a read-only target fails.
        install -m 0644 "$out/results-2025.json" "$target"
        echo "[dev] data ready at $target"

        # Watch the data sources: the Python lib + this year's process.py,
        # commentary.md, and survey.yaml. .md/.yaml matter because commentary and
        # the schema feed the page; without them, prose edits never hot-reload.
        watchexec -e py,md,yaml -w community/2025 -w overlays/python-packages/nixos-survey-lib --postpone -- bash -c '
          out=$(nix build --no-link --print-out-paths .#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data) \
            && install -m 0644 "$out/results-2025.json" lib/site/src/content/results/results-2025.json \
            && echo "[dev] data updated"
        ' &
        watch_pid=$!
        trap 'kill $watch_pid 2>/dev/null' INT TERM EXIT

        # Reinstall when node_modules is missing, or when the lockfile is newer
        # than the last install (npm refreshes node_modules/.package-lock.json on
        # every install) — so dependency changes aren't silently skipped.
        if [ ! -d lib/site/node_modules ] || [ lib/site/package-lock.json -nt lib/site/node_modules/.package-lock.json ]; then
          echo "[dev] installing npm dependencies..."
          (cd lib/site && npm install --silent)
        fi
        (cd lib/site && npm run dev)
      )

      echo "Surveys dev shell."
      echo ""
      echo "Live dev pipeline: dev"
      echo "Run tests:         pytest overlays/python-packages/nixos-survey-lib/tests/"
      echo "Build data once:   nix build .#legacyPackages.x86_64-linux.nixos-surveys-community-2025-data"
    '';
  };
}) inputs.self.legacyPackages
