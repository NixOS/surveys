{
  runCommand,
}:

# Vendored data: a committed results-2025.json copied into the store, so the
# site builds with no access to the raw (PII) survey CSV. Regenerate the
# committed file from the CSV with `vendor-data` (see dev-shells/default.nix),
# which builds nixos-surveys-community-2025-data-from-csv and copies its output
# here. Output path ($out/results-2025.json) matches the from-csv derivation so
# nixos-surveys-site and `dev` consume either one unchanged.
runCommand "nixos-surveys-community-2025-data-0.1.0" { } ''
  mkdir -p $out
  cp ${./results-2025.json} $out/results-2025.json
''
