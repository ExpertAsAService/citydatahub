/*
Nom du script : referentiels.sql
Description : Jeu de données initial — référentiels métier (categories,
              indicateurs, sources). Idempotent et rejouable sur toute base
              ayant joué schema.sql. Le seuil_alerte est VOLONTAIREMENT
              absent : c'est un réglage opérationnel, il se pose dans
              l'admin Django, pas dans une référence.

Auteur : Eric Diologeant
Date : 21 Novembre 2026
Version : 1.0
Licence : MIT
Usage : psql -d citydatahub      -f sql/referentiels.sql
     ou : psql -d citydatahub_test -f sql/referentiels.sql
*/

-- 1. Catégories (la racine : aucune dépendance)
INSERT INTO categories (nom) VALUES
    ('meteo'),
    ('qualite_air'),
    ('mobilite')
ON CONFLICT (nom) DO NOTHING;

-- 2. Indicateurs (référencent leur catégorie par nom, jamais par id :
--    un id SERIAL n'est pas stable d'une base à l'autre)
INSERT INTO indicateurs (nom, unite, categorie_id)
SELECT v.nom, v.unite, c.id
FROM (VALUES
    ('temperature',       '°C', 'meteo'),
    ('pollution_pm25',     'µg/m³', 'qualite_air'),
    ('velos_disponibles',  'vélos', 'mobilite')
) AS v(nom, unite, categorie)
JOIN categories c ON c.nom = v.categorie
ON CONFLICT (nom) DO NOTHING;

-- 3. Sources (les quatre sources réelles du registre fournisseurs.py)
INSERT INTO sources (nom, type, description, url) VALUES
    ('meteo_paris',
     'api',
     'Météo Paris — températures horaires (Open-Meteo)',
     'https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&hourly=temperature_2m&past_days=7'),
    ('meteo_lyon',
     'api',
     'Météo Lyon — températures horaires (Open-Meteo)',
     'https://api.open-meteo.com/v1/forecast?latitude=45.75&longitude=4.85&hourly=temperature_2m&past_days=7'),
    ('qualite_air_paris',
     'api',
     'Qualité de l''air Paris — PM2.5 (Open-Meteo Air Quality)',
     'https://air-quality-api.open-meteo.com/v1/air-quality?latitude=48.85&longitude=2.35&hourly=pm2_5&past_days=7'),
    ('velo_paris_republique',
     'api',
     'Vélos disponibles — station République, Paris (opendata.paris.fr)',
     'https://opendata.paris.fr/api/explore/v2.1/catalog/datasets/velib-disponibilite-en-temps-reel/records?where=stationcode%3D%2221027%22&limit=100')
ON CONFLICT (nom) DO NOTHING;