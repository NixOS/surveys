{
  lib,
  nixos,
  nixos-surveys-community-2026-limesurvey,
}:

# A throwaway LimeSurvey with the 2026 survey imported and activated, for
# people to take rather than for assertions to run against.
#
#   echo "127.0.0.1 survey.local" | sudo tee -a /etc/hosts   # once
#   nix run .#nixos-surveys-survey-2026-preview
#   then open http://survey.local:8080
#
# nixos-surveys-limesurvey-import-test covers what the database holds after an
# import. This covers what a respondent sees: whether a 250-option dropdown is
# usable, whether the ranking widget works on a phone, whether the Chinese
# renders at the theme's font size. Those are three of the four complaints the
# 2025 free-text feedback actually produced, and none of them is visible in a
# diff.
#
# The host browses by the same name the guest uses because LimeSurvey builds
# absolute URLs from the host it is served under.
#
# NOT VERIFIED END TO END. This derivation builds, the generated script does
# carry `hostfwd=tcp::8080-:80`, the services.limesurvey block is the same one
# nixos-surveys-limesurvey-import-test exercises and passes, and
# activate_survey is a real RemoteControl method
# (remotecontrol_handle.php:506). What has not been confirmed is that the
# survey actually serves on the host's port 8080 after boot: booting an
# interactive VM was not possible where this was written. Expect to spend a
# few minutes on the first run. The two things most likely to need a fix are
# LimeSurvey's absolute URLs under a host the browser resolves differently,
# and import-survey racing the first-boot database install.
let
  machine = nixos (
    { pkgs, ... }:
    {
      networking.hostName = "survey";
      # LimeSurvey refuses hostnames without a dot.
      networking.hosts."127.0.0.1" = [ "survey.local" ];

      services.limesurvey = {
        enable = true;
        webserver = "nginx";
        nginx.virtualHost.serverName = "survey.local";
        encryptionKeyFile = pkgs.writeText "key" (lib.strings.replicate 32 "0");
        encryptionNonceFile = pkgs.writeText "nonce" (lib.strings.replicate 24 "0");
        # mkDefault so this merges with the module's own mkDefault'ed
        # config.config (tempdir, uploaddir, ...) instead of replacing it.
        # Same reasoning as the import test; read the comment there before
        # changing this.
        config.config = lib.mkDefault { RPCInterface = "json"; };
      };

      systemd.services.import-survey = {
        description = "Import and activate the 2026 survey";
        wantedBy = [ "multi-user.target" ];
        after = [
          "phpfpm-limesurvey.service"
          "nginx.service"
        ];
        serviceConfig = {
          Type = "oneshot";
          RemainAfterExit = true;
        };
        script = ''
          until ${lib.getExe pkgs.curl} --fail --silent http://survey.local/ > /dev/null; do
            sleep 1
          done
          ${lib.getExe pkgs.python3} ${./import.py} \
            http://survey.local \
            ${nixos-surveys-community-2026-limesurvey}/survey.txt
        '';
      };

      # These belong under vmVariant: build-vm.nix defines system.build.vm as
      # the vmVariant's, and only that variant imports qemu-vm.nix, so
      # virtualisation.forwardPorts does not exist at the top level.
      virtualisation.vmVariant.virtualisation = {
        memorySize = 2048;
        diskSize = 4096;
        graphics = false;
        forwardPorts = [
          {
            from = "host";
            host.port = 8080;
            guest.port = 80;
          }
        ];
      };

      services.getty.autologinUser = "root";
      system.stateVersion = "25.05";
    }
  );
in
machine.vm.overrideAttrs (old: {
  meta = (old.meta or { }) // {
    description = "Boot the 2026 survey in a throwaway LimeSurvey for review";
    mainProgram = "run-survey-vm";
  };
})
