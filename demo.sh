#!/usr/bin/env bash

# demo.sh — démonstration end-to-end reproductible
# Rejoue installation -> données -> import -> vérification -> tests
# Auteur : Eric Diologeant — Novembre 2026

set -e
cd "$(dirname "$0")"

echo "── 1. Base : schéma ───────────────────────"
psql -d citydatahub -f sql/schema.sql

echo "── 2. Données fictives (si absentes) ──────"
[ -f data/mesures_fictives.csv ] || python tests/create_customdata_csv.py --heures 20000

echo "── 3. Import (pipeline journalisé) ─────────"
python -m modules.pipeline

echo "── 4. Contenu de la base ───────────────────"
psql -d citydatahub -c "SELECT ville, indicateur, count(*), round(avg(valeur)::numeric, 1) FROM mesures GROUP BY ville, indicateur ORDER BY 1, 2;"

echo "── 5. Tests ───────────────────────────────"
pytest tests/ -q

echo "── 6. Web : python manage.py runserver puis http://127.0.0.1:8000 ──"