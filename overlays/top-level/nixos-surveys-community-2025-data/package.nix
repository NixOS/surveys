{
  stdenv,
  python3,
  requireFile,
  nixosSurveysRepoRoot,
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.nixos-survey-lib ]);

  csv = requireFile {
    name = "nix-community-survey-2025-completed-responses.csv";
    sha256 = "0wlzzkl739qbf4rkd3m2p56kbmvap65ammbhq4wr44p3cxqy60ws";
    message = ''
      The raw survey CSV is not committed (contains PII).
      Add it to the Nix store:
        nix-store --add-fixed sha256 /path/to/nix-community-survey-2025-completed-responses.csv
    '';
  };
in
stdenv.mkDerivation {
  pname = "nixos-surveys-community-2025-data";
  version = "0.1.0";

  src = nixosSurveysRepoRoot + "/community/2025";

  nativeBuildInputs = [ pythonEnv ];

  buildPhase = ''
    python process.py ${csv} results-2025.json
  '';

  installPhase = ''
    mkdir -p $out
    cp results-2025.json $out/
  '';
}
