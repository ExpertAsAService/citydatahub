#!/usr/bin/env bash
#
# Nom du script : restore_sauvegarde.sh
# Description : Restaure une sauvegarde SUR LA PRODUCTION, avec barrières :
#               affichage du dump, confirmation tapée au clavier ("citydatahub"),
#               sauvegarde de sécurité avant restauration. Ne restaure rien
#               tant que l'opérateur n'a pas dit oui explicitement.
#               Comparaison contenus avant/après pour montrer l'impact exact de l'opération.
#
# Auteur : Eric Diologeant
# Date : 22 Novembre 2026
# Version : 1.0
# Licence : MIT
# Usage : bash scripts/restore_sauvegarde.sh [chemin du dump]
#         Sans argument : restaure la dernière sauvegarde.
#

set -e

DB_PROD="citydatahub"
DESTINATION="backups"
DERNIER=$(ls -1t "$DESTINATION"/citydatahub-*.dump 2>/dev/null | head -1)
DUMP="${1:-$DERNIER}"

if [ -z "$DUMP" ] || [ ! -f "$DUMP" ]; then
    echo "ÉCHEC : dump introuvable ($DUMP)."
    exit 1
fi

echo "════════════════════════════════════════════════════════"
echo "  RESTAURATION SUR LA PRODUCTION — opération irréversible"
echo "════════════════════════════════════════════════════════"
echo "  Dump      : $DUMP"
pg_restore --list "$DUMP" | sed -n '2,4p'
echo "  Destination : $DB_PROD (PRODUCTION)"
echo "════════════════════════════════════════════════════════"
echo ""
read -r -p "Pour restaurer, taper le nom exact de la base (citydatahub) : " REPONSE
if [ "$REPONSE" != "$DB_PROD" ]; then
    echo "Confirmation absente — restauration annulée. Rien n'a changé."
    exit 1
fi

TABLES="categories indicateurs sources mesures alertes imports"

echo "── État AVANT restauration (capturé pour comparaison) ──"
declare -A AVANT
for TABLE in $TABLES; do
    AVANT[$TABLE]=$(psql -d "$DB_PROD" -Atc "SELECT count(*) FROM $TABLE;")
    echo "   $TABLE : ${AVANT[$TABLE]}"
done

echo "── Sauvegarde de sécurité de l'état AVANT ──"
SECURITE="$DESTINATION/citydatahub-avant-restore-$(date +%Y-%m-%dT%H%M%S).dump"
pg_dump -d "$DB_PROD" -Fc -f "$SECURITE"

echo "── Restauration de $DUMP sur $DB_PROD ──"
psql -d postgres -qc "SELECT pg_terminate_backend(pid) FROM pg_stat_activity
                      WHERE datname='$DB_PROD' AND pid <> pg_backend_pid();" >/dev/null
pg_restore -d "$DB_PROD" --clean --if-exists "$DUMP"

echo "── Comparaison AVANT / APRÈS restauration ──"
printf "   %-12s %12s %12s %8s\n" "table" "avant" "apres" "ecart"
ECART_GRAVE=0
for TABLE in $TABLES; do
    APRES=$(psql -d "$DB_PROD" -Atc "SELECT count(*) FROM $TABLE;")
    DIFF=$(( APRES - AVANT[$TABLE] ))
    printf "   %-12s %12s %12s %+8d\n" "$TABLE" "${AVANT[$TABLE]}" "$APRES" "$DIFF"
done
echo "   (écart négatif = lignes perdues par la restauration ; POSITIF = lignes ajoutées)"
echo "   (écart nul partout = la restauration n'a rien changé au volume : cohérent"
echo "    si le dump date du même jour)"
echo "── Si l'état AVANT doit revenir : $SECURITE ──"