#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : extracteurs.py
Description :

Auteur : Eric Diologeant
Date : 23 Octobre 2026
Version : 0.5
Licence : MIT
Usage :

"""

from typing import Any


def extracteur_open_meteo(reponse: Any) -> list[dict]:
    """Extrait date + température du format hourly d'Open-Meteo."""
    hourly = reponse["hourly"]
    return [
        {"date": t, "valeur": v}
        for t, v in zip(hourly["time"], hourly["temperature_2m"])
        if v is not None
    ]


def extracteur_qualite_air(reponse: dict) -> list[dict]:
    """Air quality open-meteo : PM2.5 horaire."""
    temps = reponse["hourly"]["time"]
    valeurs = reponse["hourly"]["pm2_5"]
    return [{"date": t, "valeur": v} for t, v in zip(temps, valeurs) if v is not None]


def extracteur_velo_paris(reponse: dict) -> list[dict]:
    """Open Data Paris Vélib : bornes disponibles par relevé."""
    mesures = []
    for enregistrement in reponse.get("results", []):
        date = enregistrement.get("duedate") or enregistrement.get("record_timestamp")
        if date and enregistrement.get("numbikesavailable") is not None:
            mesures.append(
                {
                    "date": date,
                    "valeur": float(enregistrement["numbikesavailable"]),
                }
            )
    return mesures
