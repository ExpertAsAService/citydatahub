# citydatahub.nix - intégration NixOS du projet CityDataHub
# Importé depuis /etc/nixos/configuration.nix.
# collecte planifiée (systemd timer horaire, sauvegarde journalière).

{ config, pkgs, lib, ... }:

let
  racine = "/home/ericd/citydatahub";
  bibliotheques = lib.makeLibraryPath [
    pkgs.stdenv.cc.cc.lib    # libstdc++.so.6 (numpy)
    pkgs.zlib                # libz.so.1 (pandas)
    pkgs.zstd                # libzstd.so.1 (pandas)
  ];
in
{
  # ---------------------------------------------------------------
  # Collecte planifiee : le pipeline tourne sans intervention, une
  # fois par jour (04:00), rattrapage si la machine est eteinte
  # ---------------------------------------------------------------
  systemd.services.citydatahub-pipeline = {
    description = "CityDataHub - collecte planifiee (sources -> PostgreSQL -> alertes)";
    wantedBy = [ "multi-user.target" ];
    after = [ "network-online.target" ];
    wants = [ "network-online.target" ];
    serviceConfig = {
      Type = "oneshot";
      User = "ericd";
      Group = "users";
      WorkingDirectory = racine;
    };
    environment = {
      LD_LIBRARY_PATH = bibliotheques;
    };
    path = [
      pkgs.postgresql_18
    ];
    script = ''
      ${racine}/venv/bin/python -m modules.pipeline
    '';
  };

  systemd.timers.citydatahub-pipeline = {
    description = "Declenche la collecte CityDataHub chaque jour";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*-*-* 04:00:00";
      Persistent = true;
    };
  };

  # ---------------------------------------------------------------
  # Sauvegarde quotidienne : pg_dump format compressé -Fc, une
  # instance par jour, rotation 7 jours (voir scripts/sauvegarde.sh).
  # ---------------------------------------------------------------
  systemd.services.citydatahub-sauvegarde = {
    description = "CityDataHub - sauvegarde pg_dump quotidienne (backups/, rotation 7 jours)";
    serviceConfig = {
      Type = "oneshot";
      User = "ericd";
      Group = "users";
      WorkingDirectory = racine;
    };
    path = [
      pkgs.postgresql_18
      pkgs.bash
    ];
    script = ''
      ${pkgs.bash}/bin/bash ${racine}/scripts/sauvegarde.sh
    '';
  };

  systemd.timers.citydatahub-sauvegarde = {
    description = "Declenche la sauvegarde CityDataHub chaque nuit";
    wantedBy = [ "timers.target" ];
    timerConfig = {
      OnCalendar = "*-*-* 03:15:00";
      Persistent = true;
    };
  };

  # ---------------------------------------------------------------
  # Reseau : le serveur web (Django, port 8000) doit etre joignable
  # depuis le LAN.
  # ---------------------------------------------------------------
  networking.firewall.allowedTCPPorts = [ 8000 ];
}