{

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
  };

  outputs = inputs: {
    legacyPackages = import ./legacy-packages/default.nix inputs;
    devShells = import ./dev-shells/default.nix inputs;
  };

}
