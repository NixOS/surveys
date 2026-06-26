inputs:

let
  inherit (inputs.nixpkgs-lib) lib;
  inherit (lib.fixedPoints) composeManyExtensions;
  inherit (lib.filesystem) packagesFromDirectoryRecursive;

  misc = final: prev: {
    nixosSurveysRepoRoot = ../.;
  };

  top-level = final: prev:
    packagesFromDirectoryRecursive {
      inherit (final) callPackage;
      inherit (prev) newScope;
      directory = ./top-level;
    };

  python-packages = final: prev: {
    pythonPackagesExtensions = prev.pythonPackagesExtensions ++ [
      (python-final: python-prev:
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
