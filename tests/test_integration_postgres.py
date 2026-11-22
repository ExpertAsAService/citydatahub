#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_integration_postgres.py
Description : Ces tests parlent à la VRAIE base citydatahub_test (schéma, contraintes,
              index, idempotence) : ils exécutent du SQL structurel, pas des stubs.
              Jamais la production : la fixture session_refuse de démarrer sur une base
qui s'appelle autrement que *_test.

Auteur : Eric Diologeant
Date : 22 Novembre 2026
Version : 0.8
Licence : MIT
Usage : pytest tests/test_integration_postgres.py

"""

import subprocess
from pathlib import Path

import psycopg2
import pytest

RACINE = Path(__file__).resolve().parent.parent
TEST_DB = "citydatahub_test"


def psql_test(*args: str) -> str:
    """psql vers la base de test — le SEUL canal SQL de ces tests.

    ON_ERROR_STOP : une erreur SQL fait échouer le test, pas le silence.
    """
    retour = subprocess.run(
        ["psql", "-d", TEST_DB, "-v", "ON_ERROR_STOP=1", *args],
        capture_output=True,
        text=True,
        cwd=RACINE,
        check=True,
    )
    return retour.stdout


@pytest.fixture(scope="session")
def base_test():
    """Prend la base de test à l'état connu : reset, schéma, référentiels.

    Garde-fou anti-production : vérifie SUR LA CONNEXION ELLE-MÊME que
    la base ciblée s'appelle *_test avant d'écrire quoi que ce soit.
    """
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT current_database();")
            nom = curseur.fetchone()[0]
    assert nom.endswith("_test"), (
        f"Sécurité : ces tests doivent cibler une base *_test, pas {nom!r}."
    )
    psql_test("-f", "sql/reinitialisation.sql")
    psql_test("-f", "sql/schema.sql")
    psql_test("-f", "sql/referentiels.sql")
    yield


def test_reset_etat_connu(base_test):
    """Reset -> état de référence : 3 catégories, 3 indicateurs, 4 sources."""
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(
                "SELECT (SELECT count(*) FROM categories), "
                "(SELECT count(*) FROM indicateurs), "
                "(SELECT count(*) FROM sources);"
            )
            assert curseur.fetchone() == (3, 3, 4)


def test_schema_idempotent(base_test):
    """Rejouer schema.sql + referentiels.sql ne crée ni ne perd rien."""
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT count(*) FROM categories;")
            avant = curseur.fetchone()[0]
            curseur.execute("SELECT count(*) FROM mesures;")
            mesures_avant = curseur.fetchone()[0]
    psql_test("-f", "sql/schema.sql")
    psql_test("-f", "sql/referentiels.sql")
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute("SELECT count(*) FROM categories;")
            assert curseur.fetchone()[0] == avant
            curseur.execute("SELECT count(*) FROM mesures;")
            assert curseur.fetchone()[0] == mesures_avant


def test_unicite_mesure(base_test):
    """Règle métier exécutoire : (ville, indicateur, date) unique.

    Le pipeline écrit ON CONFLICT DO NOTHING : un re-run ne peut pas
    dupliquer une mesure — ici le crash-test le prouve en doublonnant
    volontairement.
    """
    ligne_sql = (
        "INSERT INTO mesures (date, valeur, ville, indicateur) "
        "VALUES ('2026-11-22T15:00:00Z', 12.5, 'Paris', 'temperature') "
        "ON CONFLICT DO NOTHING;"
    )
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            curseur.execute(ligne_sql)
            curseur.execute(ligne_sql)  # le doublon volontaire
            curseur.execute(
                "SELECT count(*) FROM mesures "
                "WHERE ville = 'Paris' AND indicateur = 'temperature';"
            )
            assert curseur.fetchone()[0] == 1  # le second INSERT n'a rien doublé


def test_fk_alertes(base_test):
    """Intégrité référentielle : alertes.mesure_id -> mesures.id.

    Une alerte sur une mesure inexistante est rejetée par la base
    elle-même — la contrainte est exécutoire, pas décorative.
    """
    with psycopg2.connect(dbname=TEST_DB) as connexion:
        with connexion.cursor() as curseur:
            with pytest.raises(psycopg2.errors.ForeignKeyViolation):
                curseur.execute(
                    "INSERT INTO alertes "
                    "(mesure_id, indicateur_id, seuil, valeur, date_mesure) "
                    "SELECT 999999999, id, 9.5, 12.6, now() "
                    "FROM indicateurs LIMIT 1;"
                )


def test_detection_idempotente(base_test):
    """detecte_alertes rejoué ne duplique pas (UNIQUE mesure_id).

    Autonome : la base est purgée ici, le test sera indépendant de l'ordre.
    """
    from modules.stockage.stockage_postgres import stockage_postgres

    psql_test(
        "-c",
        "TRUNCATE alertes, mesures RESTART IDENTITY CASCADE;",
    )
    stockage = stockage_postgres(base=TEST_DB)
    psql_test(
        "-c",
        "UPDATE indicateurs SET seuil_alerte = 9.5 WHERE nom = 'temperature';",
    )
    psql_test(
        "-c",
        "INSERT INTO mesures (date, valeur, ville, indicateur) "
        "VALUES ('2026-11-22T16:00:00Z', 15.0, 'Paris', 'temperature') "
        "ON CONFLICT DO NOTHING;",
    )
    premier = stockage.detecte_alertes()
    second = stockage.detecte_alertes()
    assert premier == 1   # la 15.0 > seuil 9.5 : une alerte, une seule
    assert second == 0    # rejouer ne peut pas la doubler