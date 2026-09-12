{
  description = "NixOS community surveys";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs?ref=nixos-unstable";
    nixpkgs-lib.url = "github:nix-community/nixpkgs.lib";
    treefmt-nix.inputs.nixpkgs.follows = "nixpkgs";
    treefmt-nix.url = "github:numtide/treefmt-nix";
  };

  outputs = inputs: {
    checks = import ./checks inputs;
    devShells = import ./devShells inputs;
    formatter = import ./formatter inputs;
    formatterModule = import ./formatterModule inputs;
    legacyPackages = import ./legacyPackages inputs;
    overlays = import ./overlays inputs;
  };
}
