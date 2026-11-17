#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : conftest.py
Description : test

Auteur : Eric Diologeant
Date : 23 Octobre 2026
Version : 0.1
Licence : MIT
Usage :

"""

import pytest


CSV_VALIDE = """date,valeur,indicateur,ville
2026-10-01 10:00,18.5,temperature,Rouen
2026-10-01 11:00,19.0,temperature,Paris
2026-10-01 12:00,pas-un-nombre,temperature,Paris
2026-10-01 13:00,,temperature,Paris
2026-10-02 10:00,21.2,temperature,Lyon
"""

CSV_MAUVAIS_FORMAT = """jour,mesure
2026-10-01,18.5
"""


@pytest.fixture
def csv_valide(tmp_path):
    chemin = tmp_path / "mesures.csv"
    chemin.write_text(CSV_VALIDE)
    return chemin


@pytest.fixture
def csv_mauvais_format(tmp_path):
    chemin = tmp_path / "mauvais.csv"
    chemin.write_text(CSV_MAUVAIS_FORMAT)
    return chemin


@pytest.fixture
def csv_vide(tmp_path):
    chemin = tmp_path / "vide.csv"
    chemin.write_text("")
    return chemin


@pytest.fixture
def stockage_factice(tmp_path):
    """Remplace la base par un stub en mémoire : renvoie le nombre de lignes."""
    from modules.stockage.stockage_postgres import stockage_postgres

    class stockage_stub(stockage_postgres):
        def __init__(self):
            self.insere_lignes = 0

        def insere(self, lot):
            self.insere_lignes += len(lot)
            return len(lot)

    return stockage_stub()


import pytest
from django.db import connection


@pytest.fixture(autouse=True)
def table_mesures(db):
    with connection.cursor() as curseur:
        curseur.execute(
            """
            CREATE TABLE IF NOT EXISTS mesures (
                id SERIAL PRIMARY KEY,
                date TIMESTAMPTZ,
                valeur DOUBLE PRECISION,
                ville TEXT,
                indicateur TEXT,
                collecte_le TIMESTAMPTZ
            );
        """
        )
