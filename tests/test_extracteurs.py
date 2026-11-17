#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_extracteurs.py
Description : Test des extracteurs : chaque format d'API lu avec un JSON figé (aucun réseau)

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.7
Licence : MIT
Usage : pytest tests/test_extracteurs.py -v

"""

from modules.sources.extracteurs import (
    extracteur_open_meteo,
    extracteur_qualite_air,
    extracteur_velo_paris,
)


class TestExtracteurOpenMeteo:
    def test_extraction_normale(self):
        reponse = {
            "hourly": {
                "time": ["2026-10-01T10:00", "2026-10-01T11:00"],
                "temperature_2m": [18.5, 19.0],
            }
        }
        mesures = extracteur_open_meteo(reponse)
        assert len(mesures) == 2
        assert mesures[0] == {"date": "2026-10-01T10:00", "valeur": 18.5}

    def test_valeurs_nulles_filtrees(self):
        reponse = {
            "hourly": {
                "time": ["10:00", "11:00", "12:00"],
                "temperature_2m": [18.5, None, 20.0],
            }
        }
        assert len(extracteur_open_meteo(reponse)) == 2

    def test_reponse_vide(self):
        assert (
            extracteur_open_meteo({"hourly": {"time": [], "temperature_2m": []}}) == []
        )


class TestExtracteurQualiteAir:
    def test_extraction_normale(self):
        reponse = {
            "hourly": {
                "time": ["10:00", "11:00"],
                "pm2_5": [12.3, None],
            }
        }
        mesures = extracteur_qualite_air(reponse)
        assert len(mesures) == 1
        assert mesures[0] == {"date": "10:00", "valeur": 12.3}

    def test_reponse_vide(self):
        assert extracteur_qualite_air({"hourly": {"time": [], "pm2_5": []}}) == []


class TestExtracteurVeloParis:
    def test_extraction_normale(self):
        """duedate OU record_timestamp ; numbikesavailable requis."""
        reponse = {
            "results": [
                {"duedate": "2026-10-01T10:00", "numbikesavailable": 12},
                {"record_timestamp": "2026-10-01T10:05", "numbikesavailable": 5},
                {"duedate": "2026-10-01T10:10"},  # pas de valeur -> écarté
                {"numbikesavailable": 3},  # pas de date -> écarté
            ]
        }
        mesures = extracteur_velo_paris(reponse)
        assert len(mesures) == 2
        assert mesures[0] == {"date": "2026-10-01T10:00", "valeur": 12.0}

    def test_reponse_vide(self):
        assert extracteur_velo_paris({"results": []}) == []
