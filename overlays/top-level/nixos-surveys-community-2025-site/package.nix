{
  buildNpmPackage,
  nixos-surveys-community-2025-data,
  nixosSurveysRepoRoot,
}:

buildNpmPackage {
  pname = "nixos-surveys-community-2025-site";
  version = "0.1.0";

  src = nixosSurveysRepoRoot + "/lib/site";

  # Filled by the first failing build (see Step 2).
  npmDepsHash = "sha256-ivA848iaFenVZz5quN2KrifrpuJcYINTzWC8vaL6C/Q=";

  preBuild = ''
    mkdir -p src/content/results
    cp ${nixos-surveys-community-2025-data}/results-2025.json src/content/results/results-2025.json
  '';

  buildPhase = ''
    runHook preBuild
    npx astro check
    npx astro build
    runHook postBuild
  '';

  installPhase = ''
    mkdir -p $out
    cp -r dist/* $out/
  '';
}
