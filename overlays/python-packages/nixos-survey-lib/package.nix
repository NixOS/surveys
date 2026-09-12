{
  lib,
  buildPythonPackage,
  setuptools,
  polars,
  pytestCheckHook,
}:

let
  inherit (lib.trivial) importTOML;
  pyproject = importTOML ./pyproject.toml;
in
buildPythonPackage {
  inherit (pyproject.project) name version;
  pyproject = true;
  src = ./.;

  build-system = [ setuptools ];
  dependencies = [
    polars
  ];

  nativeCheckInputs = [ pytestCheckHook ];
  pythonImportsCheck = [ "nixos_survey_lib" ];
}
