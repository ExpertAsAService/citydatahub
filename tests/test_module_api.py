#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : /test_module_api.py
Description : test 

Auteur : Eric Diologeant
Date : 31 Octobre 2026
Version : 0.1
Licence : MIT
Usage : pytest tests/test_module_api.py -v

"""

from unittest.mock import MagicMock

import pytest
import requests

from modules.sources.module_api import erreur_api, source_api
from modules.sources.extracteurs import extracteur_open_meteo

REPONSE_METEO = {
    "hourly": {
        "time": ["2026-10-01T10:00", "2026-10-01T11:00"],
        "temperature_2m": [18.5, 19.0],
    }
}


class TestSourceApi:
    def test_extraction(self, monkeypatch):
        """Simule une réponse HTTP 200 et vérifie la normalisation."""
        source = source_api("https://exemple.fr/api",
                           extracteur=extracteur_open_meteo,
                           nom="temperature", ville="Paris")
        fausse_reponse = MagicMock()
        fausse_reponse.raise_for_status.return_value = None
        fausse_reponse.json.return_value = REPONSE_METEO
        monkeypatch.setattr(requests, "get",
                           lambda *a, **kw: fausse_reponse)

        lot = next(source.recupere_data())
        assert len(lot) == 2
        assert lot.iloc[0]["valeur"] == 18.5
        assert (lot["ville"] == "Paris").all()    # ville injectée par la source
        assert (lot["indicateur"] == "temperature").all()   # sémantique, sans suffixe

    def test_api_indisponible(self, monkeypatch):
        """Simule une panne réseau persistante -> erreur_api."""
        source = source_api("https://exemple.fr/api",
                           extracteur=extracteur_open_meteo,
                           tentatives=2)
        def panne(*args, **kwargs):
            raise requests.ConnectionError("pas de réseau")
        monkeypatch.setattr(requests, "get", panne)

        with pytest.raises(erreur_api, match="tentatives"):
            next(source.recupere_data())

    def test_donnees_vides(self, monkeypatch):
        """Extracteur rend une liste VIDE -> erreur métier, sans toucher au réseau."""
        source = source_api("https://exemple.fr/api",
                           extracteur=lambda r: [],
                           nom="vide")
        # on simule la RÉPONSE, pas le transport : ce test cible la
        # branche « aucune donnée extraite » de recupere_data
        monkeypatch.setattr(source, "requete_api", lambda: {"hourly": {}})
        with pytest.raises(erreur_api, match="Aucune donnée"):
            next(source.recupere_data())