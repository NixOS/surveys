inputs:

let
  inherit (inputs.nixpkgs-lib.lib.attrsets) genAttrs;

  systems = [ "x86_64-linux" "aarch64-linux" "aarch64-darwin" ];
in
genAttrs systems (system:
  import inputs.nixpkgs {
    inherit system;
    overlays = [ inputs.self.overlays.default ];
  }
)
