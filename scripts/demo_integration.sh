#!/usr/bin/env bash
#
# Nom du script : demo_integration.sh
# Description : Crash-tests structurels EN DIRECT sur la base de test —
#               la version publique de tests/test_integration_postgres.py.
#               Schéma rejouable, contraintes exécutoires, détection
#               idempotente : ce que pytest verrouille, ce script le montre.
#
# Auteur : Eric Diologeant
# Date : 22 Novembre 2026
# Version : 1.0
# Licence : MIT
# Usage : bash scripts/demo_integration.sh
#         (cible codée en dur : citydatahub_test — jamais la production)
#

set -e
cd "$(dirname "$(readlink -f "$0")")/.."

DB="citydatahub_test"
PSQL="psql -d $DB -v ON_ERROR_STOP=1"

echo "── 1. État connu : reinitialisation + schéma + référentiels ──"
$PSQL -f sql/reinitialisation.sql
$PSQL -f sql/schema.sql
$PSQL -f sql/referentiels.sql
$PSQL -c "SELECT (SELECT count(*) FROM categories) AS cats, (SELECT count(*) FROM indicateurs) AS ind, (SELECT count(*) FROM sources) AS src;"
# attendu : 3 / 3 / 4

echo ""
echo "── 2. Idempotence du schéma : rejeu de schema.sql ──"
$PSQL -f sql/schema.sql
$PSQL -c "SELECT count(*) AS mesures_apres_rejeu FROM mesures;"
# attendu : inchangé

echo ""
echo "── 3. Règle métier : une mesure (ville, indicateur, date) unique ──"
$PSQL -c "INSERT INTO mesures (date, valeur, ville, indicateur)
          VALUES ('2026-11-22T15:00:00Z', 12.5, 'Paris', 'temperature')
          ON CONFLICT DO NOTHING;"
$PSQL -c "INSERT INTO mesures (date, valeur, ville, indicateur)
          VALUES ('2026-11-22T15:00:00Z', 12.5, 'Paris', 'temperature')
          ON CONFLICT DO NOTHING;"   # le doublon volontaire
$PSQL -c "SELECT count(*) AS paris_temperature FROM mesures
          WHERE ville='Paris' AND indicateur='temperature';"
# attendu : 1 — le second INSERT a été absorbé, pas de doublon

echo ""
echo "── 4. Intégrité : alertes.reference mesures (FK exécutoire) ──"
$PSQL -c "UPDATE indicateurs SET seuil_alerte = 9.5 WHERE nom = 'temperature';" >/dev/null
$PSQL -c "INSERT INTO alertes (mesure_id, indicateur_id, seuil, valeur, date_mesure)
          SELECT 999999999, id, 9.5, 12.6, now() FROM indicateurs LIMIT 1;" \
  && { echo "   ÉCHEC INATTENDU : la FK aurait dû rejeter."; exit 1; } \
  || echo "   Rejet attendu — violation de FK : la base se défend toute seule."

echo ""
echo "── 5. Détection d'alertes : idempotence ──"
$PSQL -c "INSERT INTO mesures (date, valeur, ville, indicateur)
          VALUES ('2026-11-22T16:00:00Z', 15.0, 'Paris', 'temperature')
          ON CONFLICT DO NOTHING;" >/dev/null
$PSQL -f sql/alertes.sql
$PSQL -f sql/alertes.sql   # rejoué : doit rendre INSERT 0 0
$PSQL -c "SELECT count(*) AS alertes FROM alertes;"
# attendu : 2 alertes (12.5 et 15.0 > 9.5), et le SECOND passage INSERT 0 0

echo ""
echo "── Structure saine, contraintes exécutoires, tout est rejouable. ──"