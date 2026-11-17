#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : fournisseurs.py
Description :

Auteur : Eric Diologeant
Date : 23 Octobre 2026
Version : 0.5
Licence : MIT
Usage :

"""

from .extracteurs import (
    extracteur_open_meteo,
    extracteur_qualite_air,
    extracteur_velo_paris,
)


def _open_meteo_meteo(ville: str, lat: float, lon: float) -> dict:
    return {
        "url": (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&hourly=temperature_2m&past_days=7"
        ),
        "extracteur": extracteur_open_meteo,
        "nom": "temperature",
        "ville": ville,
    }


def _open_meteo_air(ville: str, lat: float, lon: float) -> dict:
    return {
        "url": (
            "https://air-quality-api.open-meteo.com/v1/air-quality"
            f"?latitude={lat}&longitude={lon}"
            "&hourly=pm2_5&past_days=7"
        ),
        "extracteur": extracteur_qualite_air,
        "nom": "pollution_pm25",
        "ville": ville,
    }


def _velo_paris(stationcode: int, ville: str = "Paris") -> dict:
    return {
        "url": (
            "https://opendata.paris.fr/api/explore/v2.1/"
            f"catalog/datasets/velib-disponibilite-en-temps-reel/records"
            f"?where=stationcode%3D%22{stationcode}%22&limit=100"
        ),
        "extracteur": extracteur_velo_paris,
        "nom": "velos_disponibles",
        "ville": ville,
    }


FOURNISSEURS = {
    "meteo_paris": _open_meteo_meteo("Paris", 48.85, 2.35),
    "meteo_lyon": _open_meteo_meteo("Lyon", 45.75, 4.85),
    "qualite_air_paris": _open_meteo_air("Paris", 48.85, 2.35),
    "velo_paris_republique": _velo_paris(stationcode="21027"),
}


def creer_source(cle: str) -> "source_api":
    """Sélectionne un fournisseur du registre et rend la source prête."""
    from .module_api import source_api

    conf = FOURNISSEURS[cle]
    return source_api(
        url=conf["url"],
        extracteur=conf["extracteur"],
        nom=conf["nom"],
        ville=conf["ville"],
    )


COMBINAISONS = {
    ("meteo", "Paris"): "meteo_paris",
    ("meteo", "Lyon"): "meteo_lyon",
    ("qualite_air", "Paris"): "qualite_air_paris",
    ("velo", "Paris"): "velo_paris_republique",
}
