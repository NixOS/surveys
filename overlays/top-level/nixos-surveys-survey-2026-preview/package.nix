{
  lib,
  nixos,
  nixos-surveys-community-2026-limesurvey,
}:

# A throwaway LimeSurvey with the 2026 survey imported and activated, for
# people to take rather than for assertions to run against.
#
#   nix run .#nixos-surveys-survey-2026-preview
#   then open http://localhost:8080
#
# nixos-surveys-limesurvey-import-test covers what the database holds after an
# import. This covers what a respondent sees: whether a 250-option dropdown is
# usable, whether the ranking widget works on a phone, whether the Chinese
# renders at the theme's font size. Those are three of the four complaints the
# 2025 free-text feedback actually produced, and none of them is visible in a
# diff.
#
# The vhost is nginx's default server, so it answers whatever Host header the
# browser sends and the host side needs no /etc/hosts entry. That matters on
# NixOS, where /etc/hosts is generated and read-only. survey.local stays as the
# guest-internal name because the import service below calls LimeSurvey over
# HTTP during boot; LimeSurvey's publicurl is a relative baseUrl, so link
# generation does not depend on which name the browser used.
#
# The first run needs about half a minute while LimeSurvey installs its
# database; the import service waits for it.
#
# Verified in a two-node NixOS test: the survey imports and activates, a
# request from a second machine reaches nginx with a `Host: localhost` header,
# the landing page lists the survey, and /index.php/2026 renders. A negative
# control with port 80 closed confirms the request is refused, so the firewall
# rule above is doing the work.
#
# The second machine is not optional. A request a machine makes to its own
# address routes over `lo`, which the firewall exempts, so it succeeds whether
# or not port 80 is open. Two earlier checks were written that way and proved
# nothing.
let
  machine = nixos (
    { pkgs, ... }:
    {
      networking.hostName = "survey";
      # LimeSurvey refuses hostnames without a dot.
      networking.hosts."127.0.0.1" = [ "survey.local" ];

      # QEMU's hostfwd delivers to the guest's virtual NIC, not to loopback,
      # so the default firewall drops it and the forwarded port answers
      # nothing. Loopback is exempt, which is why a curl from inside the VM
      # succeeds while the host sees a closed port.
      networking.firewall.allowedTCPPorts = [ 80 ];

      services.limesurvey = {
        enable = true;
        webserver = "nginx";
        nginx.virtualHost.serverName = "survey.local";
        nginx.virtualHost.default = true;
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
            ${nixos-surveys-community-2026-limesurvey}/survey.txt \
            http://localhost:8080
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
