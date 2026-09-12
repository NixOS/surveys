inputs:
let

  inherit (inputs.nixpkgs-lib)
    lib
    ;

  inherit (lib.attrsets)
    mapAttrs
    ;

  inherit (lib.trivial)
    const
    flip
    ;

in
mapAttrs (flip (
  const (system: {

    formatting = inputs.self.formatterModule.${system}.config.build.check inputs.self;

  })
)) inputs.self.legacyPackages
