/* 
Nom du script : schema.sql
Description : Création du schéma de la table des mesures, ajout des informùations pour créer la base de test

Auteur : Eric Diologeant
Date : 02 Novembre 2026
Version : 1.1
Licence : MIT
Usage : psql -d citydatahub -f sql/schema.sql
Usage : psql -d citydatahub_test -f sql/schema.sql
Usage docs : psql -d citydatahub -c "\d+ mesures"
Usage docs : psql -d citydatahub_test -c "\d+ mesures"


*/

CREATE TABLE IF NOT EXISTS mesures (
    id          BIGSERIAL PRIMARY KEY,
    date        TIMESTAMPTZ   NOT NULL,
    valeur      DOUBLE PRECISION NOT NULL,
    ville       TEXT          NOT NULL,
    indicateur  TEXT          NOT NULL,
    -- traçabilité : quand cette ligne a-t-elle été insérée dans la base ?
    collecte_le TIMESTAMPTZ   NOT NULL DEFAULT now()
);

-- L'index qui sert TOUS les cas d'usage :
CREATE INDEX IF NOT EXISTS idx_mesures_recherche
    ON mesures (ville, indicateur, date);

-- Un contrôle d'intégrité métier : pas de doublon mesure/ville/date.
CREATE UNIQUE INDEX IF NOT EXISTS idx_mesures_unique
    ON mesures (ville, indicateur, date);

-- ── Documentation de la base (visible via \d+ mesures) ──────────────
COMMENT ON TABLE mesures IS
    'Mesures au format commun CityDataHub : {date, valeur, ville, indicateur}. '
    'Une ligne = une mesure d''un indicateur, pour une ville, à un instant.';

COMMENT ON COLUMN mesures.id IS
    'Identifiant technique auto-incrémenté (BIGSERIAL) — sans sens métier, '
    'stable même si la règle d''unicité évolue.';

COMMENT ON COLUMN mesures.date IS
    'Instant de la MESURE, normalisé en UTC (TIMESTAMPTZ : converti au '
    'fuseau demandé à la lecture — réconcilie les conventions des APIs).';

COMMENT ON COLUMN mesures.valeur IS
    'Valeur de la mesure en float64 (DOUBLE PRECISION) — alignée sur pandas, ';

COMMENT ON COLUMN mesures.ville IS
    'Ville de la mesure, texte libre volontairement (pas de référentiel : ';

COMMENT ON COLUMN mesures.indicateur IS
    'Sémantique de la mesure : temperature, pollution_pm25, ';

COMMENT ON COLUMN mesures.collecte_le IS
    'Horodatage de l''INSERTION de la ligne (DEFAULT now()) — traçabilité ';

COMMENT ON INDEX idx_mesures_recherche IS
    'Index de lecture : sert les requêtes WHERE ville/indicateur ';

COMMENT ON INDEX idx_mesures_unique IS
    'Règle métier exécutoire : une mesure (ville, indicateur, date) est '
    'unique par nature — un re-run du pipeline ne peut pas dupliquer.';

COMMENT ON SCHEMA public IS
    'CityDataHub : sources CSV/API -> format commun -> PostgreSQL.';