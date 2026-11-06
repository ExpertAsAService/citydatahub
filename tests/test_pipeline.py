#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_pipeline.py
Description : test

Auteur : Eric Diologeant
Date : 5 Novembre 2026
Version : 0.1
Licence : MIT
Usage : pytest tests/test_pipeline.py -v

"""
from unittest.mock import MagicMock

import pandas as pd
import pytest

from modules.sources.module_api import erreur_api
from modules.pipeline import execute

def test_independance_source(stockage_factice):
    source_ok = MagicMock()
    source_ok.recupere_data.return_value = iter([pd.DataFrame({
        "date": ["2026-10-01"], "valeur": [1.0],
        "ville": ["Paris"], "indicateur": ["temperature"],
    })])
    source_ko = MagicMock()
    source_ko.recupere_data.side_effect = erreur_api("Échec API")

    bilan = execute(
        {"ok": lambda: source_ok, "ko": lambda: source_ko},
        stockage_factice,
    )
    assert bilan["ok"]["lignes"] == 1
    assert bilan["ok"]["erreur"] is None
    assert "Échec" in bilan["ko"]["erreur"]