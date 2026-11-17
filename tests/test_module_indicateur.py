#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_module_indicateur.py
Description : test

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.6
Licence : MIT
Usage : pytest tests/test_module_indicateur.py -v

"""

import pytest
from modules.indicateur.module_indicateur import Indicateur

class TestIndicateur:
    def test_creation_valide(self):
        i = Indicateur("temperature", "°C", "meteo", seuil_alerte=35.0)
        assert i.nom == "temperature" and i.unite == "°C"

    def test_nom_vide_rejete(self):
        with pytest.raises(ValueError):
            Indicateur("", "°C")

    def test_en_alerte(self):
        i = Indicateur("temperature", "°C", "meteo", seuil_alerte=35.0)
        assert i.en_alerte(36) is True
        assert i.en_alerte(35) is False        # strict — à figer par le test
        assert i.en_alerte(34.9) is False

    def test_sans_seuil_jamais_en_alerte(self):
        i = Indicateur("frequentation", "personnes")
        assert i.en_alerte(10_000) is False