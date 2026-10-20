#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_api.py
Description : Hérite de module_base.py, interroge une API open data

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.2
Licence : MIT
Usage : 

"""

import sys
import argparse
import json
import requests
import pandas as pd

from typing import Iterator
from module_base import source_data

FORMAT_API = {"date", "valeur"}

class erreur_api(Exception):
    # To be define if necessary
    pass

class source_api(source_data):
    # Traitement d'une api, 
    # Sortie selon un format utilisable, nettoyage des lignes incorrecte

    def __init__(self, url: str, nom: str = "", description: str = ""):
        self.url = url
        self.verifie_api()
        super().__init__(nom=nom or self.url, description=description)
    
    def verifie_api(self) -> None:
        # Vérifie la cohérence de l'URL avant toute requête.
        if not self.url.startswith(("http://", "https://")):
            raise erreur_api(f"URL invalide (schéma manquant) : {self.url}")
        try:
            from urllib.parse import urlparse
            if not urlparse(self.url).netloc:
                raise erreur_api(f"URL sans nom de domaine : {self.url}")
        except ValueError as e:
            raise erreur_api(f"URL illisible : {e}") from None

    def recupere_data(self) -> pd.DataFrame:
        # 1 source API - A développer
        # Vérification du retour http  
        try:
            reponse = requests.get(self.url, timeout=10)
            reponse.raise_for_status()
        except requests.Timeout:
            raise erreur_api(f"Délai dépassé : {self.url}") from None
        except requests.RequestException as e:
            raise erreur_api(f"Requête impossible ({e}) : {self.url}") from None

        # Test sur le format de la réponse et conversion
        try:
            donnees = reponse.json()
            hourly = donnees["hourly"]
            lot = pd.DataFrame({
                "date": hourly["time"],
                "valeur": hourly["temperature_2m"],
            })
        except (json.JSONDecodeError, ValueError) as e:
            raise erreur_api(f"Réponse non JSON : {e}") from None
        except KeyError:
            raise erreur_api(
                f"Bloc 'hourly' incomplet — clés reçues : {list(donnees)}"
            ) from None

        return self.normalise_data(lot)


    def normalise_data(self, lot: pd.DataFrame) -> pd.DataFrame:
        # Mets en forme le retour en fonction du FORMAT, vérifie le cohérence des valeurs et supprime les enregistrements incorrects.
        self.verifie_frame_valide(lot)

        correct = (
            lot.assign(
                date=pd.to_datetime(lot["date"], errors="coerce"),
                valeur=pd.to_numeric(lot["valeur"], errors="coerce")
            )
            .dropna(subset=["date", "valeur"])
            .loc[lambda d: d["valeur"].isin([float("inf"), float("-inf")]) == False]
            .assign(ville="paris",indicateur="température")
            .reset_index(drop=True)
        )
        return correct[["date", "valeur", "ville", "indicateur"]]

    def verifie_frame_valide(self, lot: pd.DataFrame) -> None:
        manquantes = FORMAT_API - set(lot.columns)
        if manquantes:
            raise erreur_api(
                f"L'extracteur doit produire 'date' et 'valeur', "
                f"reçu : {list(lot.columns)} (manquant : {sorted(manquantes)})"              )

if __name__ == "__main__":

    """ 
    Usage : python module_api.py [--url URL] OR [--latitude F] [--longitude F]
    """

    # Information de base trouvée sur le site https://open-meteo.com/
    #url = ("https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m")
    #url = ("https://api.open-meteo.com/v1/forecast?latitude=48.85&longitude=2.35&hourly=temperature_2m")
    
    parseur = argparse.ArgumentParser(description="Interroge l'API Open-Meteo et affiche les températures")
    parseur.add_argument("--latitude", type=float, default=48.85, help="latitude (défaut : Paris)")
    parseur.add_argument("--longitude", type=float, default=2.35, help="longitude (défaut : Paris)")
    parseur.add_argument("--url", default=None, help="URL complète (surclasse latitude/longitude)")
    args = parseur.parse_args()

    url = args.url or (
        f"https://api.open-meteo.com/v1/forecast?latitude={args.latitude}&longitude={args.longitude}&hourly=temperature_2m"
    )

    try:
        source = source_api(url)
        df = source.recupere_data()

        print(f"{'='*60}")
        print(f" Températures prévues — {len(df)} relevés")
        print(f"{'='*60}")
        print(df.to_string(index=False, max_rows=10))

        print(f"\nMin    : {df['valeur'].min():.1f} °C")
        print(f"Max    : {df['valeur'].max():.1f} °C")
        print(f"Moyenne: {df['valeur'].mean():.1f} °C")

    except erreur_api as erreur:
        print(f" {erreur}", file=sys.stderr)
        sys.exit(1)