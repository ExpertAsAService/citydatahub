#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_stockage_idempotence.py
Description :   Test d'idempotence du stockage : re-collecter le même lot
                ne crée pas de doublon (ON CONFLICT DO NOTHING).
                Tourne sur citydatahub_test — JAMAIS sur la base de production.

Auteur : Eric Diologeant
Date : 16 Novembre 2026
Version : 0.2
Licence : MIT
Usage : pytest tests/test_stockage_idempotence.py -v
"""

import pandas as pd

from modules.stockage.stockage_postgres import stockage_postgres


@pytest.fixture
def lot_factice():
    """Un lot au format commun : 2 mesures, dates fixes et déterministes.
    Nettoie la base de test avant (répétabilité) et après (propreté)."""
    lot = pd.DataFrame([
        {"date": "2026-12-01T00:00:00+00:00", "valeur": 18.5,
         "ville": "Testville", "indicateur": "temperature"},
        {"date": "2026-12-02T00:00:00+00:00", "valeur": 19.0,
         "ville": "Testville", "indicateur": "temperature"},
    ])
    stockage = stockage_postgres(base="citydatahub_test")
    with stockage.moteur.connect() as conn:
        conn.connection.cursor().execute(
            "DELETE FROM mesures WHERE ville = 'Testville'")
        conn.connection.commit()
    yield lot
    with stockage.moteur.connect() as conn:
        conn.connection.cursor().execute(
            "DELETE FROM mesures WHERE ville = 'Testville'")
        conn.connection.commit()


def test_insere_deux_fois_est_idempotent(lot_factice):
    """1re passe : tout inséré. 2e passe : 0 nouvelle, aucune exception."""
    stockage = stockage_postgres(base="citydatahub_test")   # base de test !
    premiere = stockage.insere(lot_factice)
    deuxieme = stockage.insere(lot_factice)
    assert deuxieme == 0