#!/usr/bin/env bash
#
# Nom du script : sauvegarde.sh
# Description : Sauvegarde de la base citydatahub au format custom pg_dump
#               (-Fc : compressé, restaurable). Une sauvegarde par jour,
#               rotation : les 7 derniers jours sont conservés.
#
# Auteur : Eric Diologeant
# Date : 22 Novembre 2026
# Version : 1.0
# Licence : MIT
# Usage : bash scripts/sauvegarde.sh          (ou via le timer systemd 03:15)
#

set -e

DB="citydatahub"
DESTINATION="backups"
JOURS=7

mkdir -p "$DESTINATION"

FICHIER="$DESTINATION/citydatahub-$(date +%Y-%m-%d).dump"

echo "── Sauvegarde de $DB vers $FICHIER ──"
pg_dump -d "$DB" -Fc -f "$FICHIER"

echo "── Rotation : on garde $JOURS jours ──"
find "$DESTINATION" -name "citydatahub-*.dump" -mtime +$((JOURS - 1)) -delete
ls -lh "$DESTINATION"/citydatahub-*.dump