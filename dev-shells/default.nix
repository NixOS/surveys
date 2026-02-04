inputs:

let

  inherit (inputs.nixpkgs)
    lib
    ;

  inherit (lib.attrsets)
    attrValues
    mapAttrs
    ;

  inherit (lib.trivial)
    const
    ;

  inherit (inputs.self)
    legacyPackages
    ;

in

mapAttrs (const (pkgs: {

  survey-dev = pkgs.callPackage (
    {
      mkShell,
      python3,
    }:
    mkShell {

      packages = [

        (python3.withPackages (
          ps:
          attrValues {
            inherit (ps)
              altair
              anywidget
              bleach
              bokeh
              linkify-it-py
              markdown-it-py
              mdit-py-plugins
              narwhals
              numpy
              packaging
              pandas
              panel
              param
              polars
              pyarrow
              pyviz-comms
              requests
              tqdm
              typing-extensions
              vega
              ;
          }
        ))

      ];

    }
  ) { };

})) legacyPackages
