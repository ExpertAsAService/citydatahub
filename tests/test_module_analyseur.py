#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_module_analyseur.py
Description : test

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.8
Licence : MIT
Usage : pytest tests/test_module_analyseur.py -v

"""

import numpy as np
import pandas as pd
import pytest
from modules.analyseur.module_analyseur import AnalyseurDeDonnees


@pytest.fixture
def df_croissant():
    return pd.DataFrame(
        {
            "date": pd.date_range("2026-11-01", periods=30, freq="D"),
            "valeur": np.arange(30, dtype=float),
        }
    )


@pytest.fixture
def df_avec_depassement(df_croissant):
    df = df_croissant.copy()
    df.loc[0, "valeur"] = 100.0  # un pic isolé
    return df


class TestAnalyseur:
    def test_colonnes_manquantes_rejetees(self):
        with pytest.raises(ValueError):
            AnalyseurDeDonnees(pd.DataFrame({"valeur": [1.0]}))

    def test_resume(self, df_croissant):
        r = AnalyseurDeDonnees(df_croissant).resume()
        assert r["nombre"] == 30
        assert r["min"] == 0.0 and r["max"] == 29.0
        assert r["moyenne"] == pytest.approx(14.5)

    def test_tendance_croissante(self, df_croissant):
        assert AnalyseurDeDonnees(df_croissant).detecter_tendance() > 0

    def test_tendance_stable(self):
        df = pd.DataFrame(
            {"date": pd.date_range("2026-11-01", periods=30), "valeur": [20.0] * 30}
        )
        assert abs(AnalyseurDeDonnees(df).detecter_tendance()) < 1e-9

    def test_alertes_isole_le_pic(self, df_avec_depassement):
        alertes = AnalyseurDeDonnees(df_avec_depassement).generer_alertes(50)
        assert len(alertes) == 1
        assert alertes.iloc[0]["valeur"] == 100.0

    def test_rapport_sans_alerte(self, df_croissant):
        rapport = AnalyseurDeDonnees(df_croissant).rapport_alerte(1000)
        assert rapport["nombre"] == 0
        assert rapport["max"] is None and rapport["premiere_date"] is None
