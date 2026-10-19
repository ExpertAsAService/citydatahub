#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_api.py
Description : Hérite de module_base.py, interroge une API open data

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.1
Licence : MIT
Usage : 

"""

import json
import requests
import pandas as pd

from typing import Iterator
from module_base import source_data

FORMAT_API = {"date", "valeur", "ville", "indicateur"}

class erreur_api(Exception):
    # To be define if necessary
    pass

class source_api():
    # 

    def __init__(self, url: str):
        self.url = url
    
    def recupere_data(self): 
        # Effectue une requete http
        reponse = requests.get(self.url, timeout=10)
        print(f"code HTTP : {reponse.status_code}")
        print(reponse.json())

    def normalise_data(self):
        pass

if __name__ == "__main__":

    """ 
    Usage : python module_api.py
    Nomfichier: 
    """

    # Information de base trouvée sur le site https://open-meteo.com/
    url = ("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    source = source_api(url)
    source.recupere_data()
    