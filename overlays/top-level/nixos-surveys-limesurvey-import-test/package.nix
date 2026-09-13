{
  lib,
  testers,
  nixos-surveys-community-2025-limesurvey,
  nixos-surveys-community-2026-limesurvey,
}:

# Boots LimeSurvey from the nixpkgs module with the JSON-RPC interface on,
# imports the generated 2025 and 2026 survey files and the two-language golden
# fixture from the library's tests, and asserts on the result.
# Build on demand: nix build .#nixos-surveys-limesurvey-import-test
# Needs KVM (Linux only). Not part of flake checks.
testers.runNixOSTest {
  name = "nixos-surveys-limesurvey-import";

  nodes.machine =
    { pkgs, ... }:
    {
      services.limesurvey = {
        enable = true;
        webserver = "nginx";
        nginx.virtualHost.serverName = "survey.local";
        encryptionKeyFile = pkgs.writeText "key" (lib.strings.replicate 32 "0");
        encryptionNonceFile = pkgs.writeText "nonce" (lib.strings.replicate 24 "0");
        # mkDefault so this merges with the module's own mkDefault'ed
        # config.config (tempdir, uploaddir, ...) instead of replacing it.
        # Verified by evaluation. Do not "simplify" to
        #   config = lib.mkDefault { config.RPCInterface = "json"; };
        # (the module's outer set then wins and RPCInterface vanishes) or to
        # a plain definition (tempdir and uploaddir vanish).
        config.config = lib.mkDefault { RPCInterface = "json"; };
      };

      # LimeSurvey refuses hostnames without a dot.
      networking.hosts."127.0.0.1" = [ "survey.local" ];

      environment.systemPackages = [ pkgs.python3 ];
    };

  testScript = ''
    start_all()
    # limesurvey-init is a oneshot without RemainAfterExit, so it cannot be
    # waited on directly; it is ordered before phpfpm-limesurvey.
    machine.wait_for_unit("phpfpm-limesurvey.service")
    machine.wait_for_unit("nginx.service")
    machine.wait_for_open_port(80)
    machine.wait_until_succeeds("curl --fail --silent http://survey.local/ > /dev/null")
    # succeed() only logs the command's output when it fails, so log it
    # ourselves: the imported survey id and the pass line are the evidence
    # that the run actually did something.
    machine.log(
      machine.succeed(
        "python3 ${./import_check.py} http://survey.local ${nixos-surveys-community-2025-limesurvey}/survey.txt ${../../python-packages/nixos-survey-lib/tests/fixtures/limesurvey/expected_survey.txt} ${nixos-surveys-community-2026-limesurvey}/survey.txt"
      )
    )
  '';
}
