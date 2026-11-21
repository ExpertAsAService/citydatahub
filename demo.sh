#!/usr/bin/env bash

# demo.sh — démonstration end-to-end reproductible
# Rejoue installation -> référentiels -> seuil -> données -> import CSV -> vérification -> tests -> web
# Auteur : Eric Diologeant — Novembre 2026

set -e
cd "$(dirname "$0")"

echo "── 1. Base : schéma ───────────────────────"
psql -d citydatahub -f sql/schema.sql

echo "── 2. Référentiels (jeu de données initial, rejouable) ──"
psql -d citydatahub -f sql/referentiels.sql

echo "── 3. Seuil opérationnel de démo ───────────"
psql -d citydatahub -c "UPDATE indicateurs SET seuil_alerte=9.5 WHERE nom='temperature';"

echo "── 4. Données fictives (si absentes) ──────"
[ -f data/mesures_fictives.csv ] || python tests/create_customdata_csv.py --heures 20000

echo "── 5. Import pipeline (APIs, journalisé) ──"
python -m modules.pipeline

echo "── 6. Import CSV (même chemin que la vue : source_csv + stockage) ──"
DJANGO_SETTINGS_MODULE=citydatahub_web.settings python -c "
import django
django.setup()
from modules.sources import source_csv
from modules.stockage.stockage_postgres import stockage_postgres
source = source_csv('data/mesures_fictives.csv')
stockage = stockage_postgres()
lues, inserees = 0, 0
for lot in source.recupere_data():
    lues += len(lot)
    inserees += stockage.insere(lot)
alertes = stockage.detecte_alertes()
print(f'{inserees} mesures importées sur {lues} lues — {alertes} nouvelle(s) alerte(s).')
"

echo "── 7. Contenu de la base ───────────────────"
psql -d citydatahub -c "SELECT ville, indicateur, count(*), round(avg(valeur)::numeric, 1) FROM mesures GROUP BY ville, indicateur ORDER BY 1, 2;"

echo "── 8. Tests ───────────────────────────────"
pytest tests/ -q

echo "── 9. Web ──────────────────────────────────"
echo "Local : python manage.py runserver"
echo "LAN   : python manage.py runserver 0.0.0.0:8000"
echo "       (avg : ALLOWED_HOSTS += <ip> ; pare-feu NixOS : iptables -I nixos-fw -p tcp --dport 8000 -j ACCEPT)"
echo "       (le seuil de l'étape 3 prépare la détection : badge rouge attendu à l'accueil)"