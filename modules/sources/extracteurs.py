#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : extracteurs.py
Description : 

Auteur : Eric Diologeant
Date : 23 Octobre 2026
Version : 0.1
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

