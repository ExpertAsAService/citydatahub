/*
Nom du script : reinitialisation.sql
Description : Réinitialisation complète de la base métier — purge des
              données (tables métier + monitoring imports) et reposage du
              jeu de données initial (référentiels).

Auteur : Eric Diologeant
Date : 21 Novembre 2026
Version : 1.0
Licence : MIT
Usage : psql -d citydatahub      -v ON_ERROR_STOP=1 -f sql/reinitialisation.sql
     ou : psql -d citydatahub_test -v ON_ERROR_STOP=1 -f sql/reinitialisation.sql
*/

\set ON_ERROR_STOP on

BEGIN;

-- 1. Purge des données métier
TRUNCATE alertes, mesures, imports, indicateurs, categories, sources
    RESTART IDENTITY CASCADE;

-- 2. Reposage immédiat du jeu de données initial

\i sql/referentiels.sql

COMMIT;

-- 3. Run WebServer
-- python manage.py runserver 0.0.0.0:8000 &

-- 4. Modification du seuil
-- /admin/indicateurs/indicateurref/ 
-- Ajout des données fictives => mesures_fictives.csv

-- 5. Ajout des données d'alertes
-- python -m modules.pipeline