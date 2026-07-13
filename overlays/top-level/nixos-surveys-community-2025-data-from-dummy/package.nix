{
  stdenv,
  python3,
  nixosSurveysRepoRoot,
}:

# Synthetic data: generates a fake responses CSV from survey.yaml
# (deterministic, seeded — see nixos_survey_lib.synthesize) and runs the
# full pipeline on it. Lets contributors without the raw (PII) CSV run and
# iterate on process.py / nixos_survey_lib. Same output contract as the
# sibling data derivations ($out/results-2025.json); additionally ships
# the generated CSV for inspection.
let
  pythonEnv = python3.withPackages (ps: [ ps.nixos-survey-lib ]);
in
stdenv.mkDerivation {
  pname = "nixos-surveys-community-2025-data-from-dummy";
  version = "0.1.0";

  src = nixosSurveysRepoRoot + "/community/2025";

  nativeBuildInputs = [ pythonEnv ];

  buildPhase = ''
    python generate_dummy.py dummy-responses.csv
    python process.py dummy-responses.csv results-2025.json
  '';

  installPhase = ''
    mkdir -p $out
    cp results-2025.json dummy-responses.csv $out/
  '';
}
