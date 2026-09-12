{
  description = "NixOS community surveys";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    nixpkgs-lib.url = "github:nix-community/nixpkgs.lib";
  };

  outputs = inputs: {
    overlays       = import ./overlays inputs;
    legacyPackages = import ./legacyPackages inputs;
    devShells      = import ./devShells inputs;
  };
}
