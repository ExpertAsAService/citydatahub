#!/usr/bin/env bash
#
# Nom du script : verif_sauvegarde.sh
# Description : Contre-épreuve automatique de la dernière sauvegarde :
#               restaure le dernier dump dans une base jetable, compare
#               les comptages avec la production, rend un verdict, puis
#               supprime la base jetable. Sort en erreur si divergence
#               (et garde alors la base pour inspection).
#
# Auteur : Eric Diologeant
# Date : 22 Novembre 2026
# Version : 1.0
# Licence : MIT
# Usage : bash scripts/verif_sauvegarde.sh
#

set -e

DB_PROD="citydatahub"
DB_VERIF="citydatahub_verif"
DESTINATION="backups"

DERNIER=$(ls -1t "$DESTINATION"/citydatahub-*.dump 2>/dev/null | head -1)
if [ -z "$DERNIER" ]; then
    echo "ÉCHEC : aucune sauvegarde trouvée dans $DESTINATION/."
    exit 1
fi
echo "── Sauvegarde vérifiée : $DERNIER ──"

psql -d postgres -qc "DROP DATABASE IF EXISTS $DB_VERIF;"
psql -d postgres -qc "CREATE DATABASE $DB_VERIF OWNER ericd;"

echo "── Restauration dans $DB_VERIF ──"
pg_restore -d "$DB_VERIF" "$DERNIER"

TABLES="categories indicateurs sources mesures alertes imports"
ECART=0
for TABLE in $TABLES; do
    PROD=$(psql -d "$DB_PROD" -Atc "SELECT count(*) FROM $TABLE;")
    VERIF=$(psql -d "$DB_VERIF" -Atc "SELECT count(*) FROM $TABLE;")
    if [ "$PROD" = "$VERIF" ]; then
        echo "   $TABLE : $PROD = $VERIF   OK"
    else
        echo "   $TABLE : production=$PROD sauvegarde=$VERIF   ÉCART"
        ECART=1
    fi
done

if [ "$ECART" -eq 0 ]; then
    echo "── Verdict : contenu identique. La sauvegarde est bonne. ──"
    psql -d postgres -qc "DROP DATABASE $DB_VERIF;"
    echo "── Base $DB_VERIF supprimée. ──"
    exit 0
else
    echo "── Verdict : ÉCART détecté. ──"
    echo "   La base $DB_VERIF est CONSERVÉE pour inspection."
    exit 1
fi