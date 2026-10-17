{
  stdenv,
  python3,
  nixosSurveysRepoRoot,
}:

let
  pythonEnv = python3.withPackages (ps: [ ps.nixos-survey-lib ]);
in
stdenv.mkDerivation {
  pname = "nixos-surveys-nixcon-2026-limesurvey";
  version = "0.1.0";

  src = nixosSurveysRepoRoot + "/nixcon/2026";

  nativeBuildInputs = [ pythonEnv ];

  buildPhase = ''
    nixos-survey-limesurvey survey.toml -o survey.txt
  '';

  installPhase = ''
    mkdir -p $out
    cp survey.txt $out/
  '';
}
