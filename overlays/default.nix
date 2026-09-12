inputs:

let
  inherit (inputs.nixpkgs-lib) lib;
  inherit (lib.fixedPoints) composeManyExtensions;
  inherit (lib.filesystem) packagesFromDirectoryRecursive;

  misc = _final: _prev: {
    nixosSurveysRepoRoot = ../.;
  };

  top-level =
    final: prev:
    packagesFromDirectoryRecursive {
      inherit (final) callPackage;
      inherit (prev) newScope;
      directory = ./top-level;
    };

  python-packages = _final: prev: {
    pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
      (
        python-final: _python-prev:
        packagesFromDirectoryRecursive {
          inherit (python-final) callPackage newScope;
          directory = ./python-packages;
        }
      )
    ];
  };

  default = composeManyExtensions [
    misc
    top-level
    python-packages
  ];
in
{
  inherit default;
}
