#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_stockage.py
Description : test

Auteur : Eric Diologeant
Date : 5 Novembre 2026
Version : 0.1
Licence : MIT
Usage : pytest tests/test_stockage.py -v

"""
import pandas as pd
import pytest

from modules.stockage.stockage_postgres import erreur_stockage, stockage_postgres

class TestStockage:
    def test_lot_non_conforme(self):
        stockage = stockage_postgres.__new__(stockage_postgres)
        lot = pd.DataFrame({"mauvaise": [1]})
        with pytest.raises(erreur_stockage, match="colonnes"):
            stockage.insere(lot)