{
  stdenv,
  python3,
  nixosSurveysRepoRoot,
}:

# LimeSurvey import file for the 2025 community survey, generated from
# community/2025/survey.toml and its text files. Upload $out/survey.txt in
# LimeSurvey under Surveys > Create > Import.
let
  pythonEnv = python3.withPackages (ps: [ ps.nixos-survey-lib ]);
in
stdenv.mkDerivation {
  pname = "nixos-surveys-community-2025-limesurvey";
  version = "0.1.0";

  src = nixosSurveysRepoRoot + "/community/2025";

  nativeBuildInputs = [ pythonEnv ];

  buildPhase = ''
    nixos-survey-limesurvey survey.toml -o survey.txt
  '';

  installPhase = ''
    mkdir -p $out
    cp survey.txt $out/
  '';
}
