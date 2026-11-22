/*
Nom du script : schema.sql
Description : Schéma CityDataHub — table des mesures + extension
              multi-tables (categories, indicateurs, sources, alertes)
              Script idempotent : rejouable à l'identique sur les deux bases.
              Rôle unique : STRUCTURE seule — les données de référence
              vivent dans referentiels.sql.

Auteur : Eric Diologeant
Date : 21 Novembre 2026
Version : 1.3
Licence : MIT
Usage production : psql -d citydatahub -f sql/schema.sql
Usage test        : psql -d citydatahub_test -f sql/schema.sql
Usage docs        : psql -d citydatahub -c "\d+ mesures"
                    psql -d citydatahub -c "\d+ indicateurs"
*/


CREATE TABLE IF NOT EXISTS mesures (
    id          BIGSERIAL PRIMARY KEY,
    date        TIMESTAMPTZ   NOT NULL,
    valeur      DOUBLE PRECISION NOT NULL,
    ville       TEXT          NOT NULL,
    indicateur  TEXT          NOT NULL,
    collecte_le TIMESTAMPTZ   NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_mesures_recherche
    ON mesures (ville, indicateur, date);

CREATE UNIQUE INDEX IF NOT EXISTS idx_mesures_unique
    ON mesures (ville, indicateur, date);

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
    'Valeur de la mesure en float64 (DOUBLE PRECISION) — alignée sur pandas, '
    'types homogènes du DataFrame jusqu''à la base.';

COMMENT ON COLUMN mesures.ville IS
    'Ville de la mesure, texte libre volontairement (pas de référentiel : '
    'décision initiale, le format commun garantit la cohérence à la source).';

COMMENT ON COLUMN mesures.indicateur IS
    'Sémantique de la mesure : temperature, pollution_pm25, '
    'velos_disponibles — jointé par nom au référentiel indicateurs.';

COMMENT ON COLUMN mesures.collecte_le IS
    'Horodatage de l''INSERTION de la ligne (DEFAULT now()) — traçabilité '
    'gratuite au niveau stockage, sans polluer le format commun des sources.';

COMMENT ON INDEX idx_mesures_recherche IS
    'Index de lecture : sert les requêtes WHERE ville/indicateur '
    'triées par date — toutes les pages web et l''API en profitent.';

COMMENT ON INDEX idx_mesures_unique IS
    'Règle métier exécutoire : une mesure (ville, indicateur, date) est '
    'unique par nature — un re-run du pipeline ne peut pas dupliquer.';


CREATE TABLE IF NOT EXISTS categories (
    id   SERIAL PRIMARY KEY,
    nom  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS indicateurs (
    id            SERIAL PRIMARY KEY,
    nom           TEXT NOT NULL UNIQUE,
    unite         TEXT NOT NULL,
    categorie_id  INT NOT NULL REFERENCES categories(id),
    seuil_alerte  DOUBLE PRECISION 
);

CREATE TABLE IF NOT EXISTS sources (
    id          SERIAL PRIMARY KEY,
    nom         TEXT NOT NULL UNIQUE,
    type        TEXT NOT NULL, 
    description TEXT DEFAULT '',
    url         TEXT DEFAULT '' 
);

CREATE TABLE IF NOT EXISTS alertes (
    id            BIGSERIAL PRIMARY KEY,
    mesure_id     BIGINT NOT NULL REFERENCES mesures(id),
    indicateur_id INT NOT NULL REFERENCES indicateurs(id),
    seuil         DOUBLE PRECISION NOT NULL,
    valeur        DOUBLE PRECISION NOT NULL,
    date_mesure   TIMESTAMPTZ NOT NULL,
    UNIQUE (mesure_id)
);

-- Jeu de données initial : => referentiels.sql pose
-- le référentiel (categories meteo/qualite_air/mobilite, indicateurs,
-- sources miroir de fournisseurs.py). Le référentiel déduit des
-- mesures, unités 's.u.', catégorie 'environnement' par défaut — a été
-- abrogée : le schéma crée, referentiels alimente.

COMMENT ON TABLE categories IS
    'Référentiel des catégories d''indicateurs (posées par referentiels.sql) : '
    'meteo, qualite_air, mobilite.';

COMMENT ON TABLE indicateurs IS
    'Référentiel des indicateurs : nom (jointé par nom à mesures.indicateur), '
    'unité, catégorie, seuil d''alerte (NULL = jamais en alerte) — '
    'posé par referentiels.sql, le seuil se règle à l''écran (admin).';

COMMENT ON TABLE sources IS
    'Référentiel des sources persisté en base (miroir du registre '
    'fournisseurs.py) — nom = clé du registre, type api|csv, url.';

COMMENT ON TABLE alertes IS
    'Dépassements de seuil détectés : une ligne par mesure en dépassement. '
    'UNIQUE (mesure_id) : rejouer la détection ne duplique pas les alertes.';

COMMENT ON SCHEMA public IS
    'CityDataHub : sources CSV/API -> format commun -> PostgreSQL '
    '(mesures + référentiels + alertes).';


CREATE TABLE IF NOT EXISTS imports (
    id             BIGSERIAL PRIMARY KEY,
    fichier        TEXT NOT NULL,
    utilisateur    TEXT,
    lignes_lues    INTEGER DEFAULT 0,
    lignes_inserees INTEGER DEFAULT 0,
    lignes_rejetees INTEGER DEFAULT 0,
    statut         TEXT NOT NULL,          -- 'succes' | 'echec' |
    erreur         TEXT,
    date_import    TIMESTAMPTZ NOT NULL DEFAULT now()
);
COMMENT ON TABLE imports IS 'Historique des imports CSV, une ligne par tentative.';