{
  stdenv,
  python3,
  nixosSurveysRepoRoot,
}:

# LimeSurvey import file for the 2026 community survey, generated from
# community/2026/survey.toml and its text files. Upload $out/survey.txt in
# LimeSurvey under Surveys > Create > Import.
#
# Unlike 2025 this build also runs test_survey_2026.py, which asserts the
# instrument against its design spec. 23 questions were rewritten for 2026 and
# several strings are load-bearing for the analysis pipeline, so drift is
# caught here rather than in December.
let
  pythonEnv = python3.withPackages (ps: [
    ps.nixos-survey-lib
    ps.pytest
  ]);
in
stdenv.mkDerivation {
  pname = "nixos-surveys-community-2026-limesurvey";
  version = "0.1.0";

  # Both years: test_survey_2026.py asserts the carried-verbatim questions
  # byte-for-byte against community/2025, which the converter itself never
  # reads. 2025 is a few hundred kilobytes of TOML, so the wider src is free.
  src = nixosSurveysRepoRoot + "/community";

  nativeBuildInputs = [ pythonEnv ];

  buildPhase = ''
    nixos-survey-limesurvey 2026/survey.toml -o survey.txt
  '';

  doCheck = true;

  checkPhase = ''
    pytest 2026/test_survey_2026.py
  '';

  installPhase = ''
    mkdir -p $out
    cp survey.txt $out/
  '';
}
