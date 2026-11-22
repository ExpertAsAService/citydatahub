#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : conftest.py
Description : Fixtures communes des tests — fichiers CSV temporaires,
              stub de stockage sans base, et schéma de test joué depuis
              sql/schema.sql (référence unique, idempotent).

Auteur : Eric Diologeant
Date : 20 Novembre 2026
Version : 0.2
Licence : MIT
"""

from pathlib import Path

import pytest
from django.db import connection


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

        def detecte_alertes(self):
            # le stub n'a pas de base : la détection rend zéro, sans IO
            return 0

    return stockage_stub()


@pytest.fixture(autouse=True)
def schema_complet(db):
    """Crée le schéma de test en jouant sql/schema.sql — LA référence unique.

    Le script est idempotent (IF NOT EXISTS, ON CONFLICT DO NOTHING) :
    rejouable à chaque session de test, il suivra les évolutions 
    sans que ce fichier n'ait à changer.
    """
    schema = Path(__file__).resolve().parent.parent / "sql" / "schema.sql"
    with connection.cursor() as curseur:
        curseur.execute(schema.read_text())
