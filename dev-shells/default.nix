inputs:

let
  inherit (inputs.nixpkgs-lib.lib.attrsets) mapAttrs;
in
mapAttrs (system: pkgs: {
  default = pkgs.mkShell {
    packages = [
      (pkgs.python3.withPackages (ps: [ ps.polars ps.pyyaml ps.pytest ]))
      pkgs.nodejs_22
    ];

    shellHook = ''
      export PYTHONPATH=$PWD/overlays/python-packages/nixos-survey-lib:$PYTHONPATH
      echo "Surveys dev. nixos-survey-lib will be available via Nix once defined; local edits override."
      echo "Run: python community/2025/process.py <csv> <out.json>"
      echo "Tests: pytest overlays/python-packages/nixos-survey-lib/tests/"
      echo "Astro: (cd lib/site && npm install && npm run dev)"
    '';
  };
}) inputs.self.legacyPackages
