/*
Nom du script : alertes.sql
Description : Détection des dépassements de seuil — insère une ligne dans
              alertes pour chaque mesure au-dessus du seuil de son indicateur.
              Idempotent : UNIQUE(mesure_id) + ON CONFLICT DO NOTHING,
              rejouable après chaque import.

Auteur : Eric Diologeant
Date : 20 Novembre 2026
Version : 1.0
Licence : MIT
Usage : psql -d citydatahub_test -f sql/alertes.sql
     ou : psql -d citydatahub      -f sql/alertes.sql
*/

INSERT INTO alertes (mesure_id, indicateur_id, seuil, valeur, date_mesure)
SELECT m.id, i.id, i.seuil_alerte, m.valeur, m.date
FROM mesures m
JOIN indicateurs i ON i.nom = m.indicateur
WHERE i.seuil_alerte IS NOT NULL
  AND m.valeur > i.seuil_alerte
ON CONFLICT (mesure_id) DO NOTHING;