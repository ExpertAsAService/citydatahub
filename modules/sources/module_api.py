#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_api.py
Description : Hérite de module_base.py, interroge une API open data

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.3
Licence : MIT
Usage : 

"""

import sys
import time
import argparse
import json
import requests
import pandas as pd

from typing import Any, Iterator
from urllib.parse import urlparse

from .module_base import source_data

FORMAT_API = {"date", "valeur"}

class erreur_api(Exception):
    # To be define if necessary
    pass

class source_api(source_data):
    # Traitement d'une api, 
    # Sortie selon un format utilisable, nettoyage des lignes incorrecte

    def __init__(self, url: str, ville: str = "inconnue", nom: str = "", description: str = "",  extracteur=None, tentatives: int = 3, timeout: int = 10):
        self.url = url
        self.ville = ville
        self.extracteur = extracteur
        self.tentatives = tentatives
        self.timeout = timeout
        self._verifie_url()
        super().__init__(nom=nom or self.url, description=description)
        if self.extracteur is None:
            raise erreur_api(
                f"Un extracteur est requis pour {self.nom or self.url} : "
                "fonction (dict) -> list[dict] '{date, valeur}'"
            )
    
    def _verifie_url(self) -> None:
        # Vérifie la cohérence de l'URL avant toute requête.
        if not self.url.startswith(("http://", "https://")):
            raise erreur_api(f"URL invalide (schéma manquant) : {self.url}")
        try:
            if not urlparse(self.url).netloc:
                raise erreur_api(f"URL sans nom de domaine : {self.url}")
        except ValueError as e:
            raise erreur_api(f"URL illisible : {e}") from None

    def recupere_data(self) -> Iterator[pd.DataFrame]:
        # Coeur du mécanisme de récupération des données
        reponse = self.requete_api()
        databloc = self.extraire_data(reponse) # format vérifié, erreurs métier
        if not databloc:
            raise erreur_api(f"Aucune donnée extraite depuis {self.url}")
        yield self.normalise_data(pd.DataFrame(databloc))

    def extraire_data(self, reponse: Any) -> list[dict]:
        # Extraction des données
        try:
            return self.extracteur(reponse)
        except (KeyError, TypeError, AttributeError) as e:
            raise erreur_api(
            f"Format de réponse inattendu depuis {self.url} "
            f"(extrait attendu introuvable : {e!r})"
            ) from e

    def requete_api(self) -> Any:
        #  Vérification du retour http, gestion des erreurs et retry
        derniere_erreur: Exception | None = None
        for tentative in range(1, self.tentatives + 1):
            try:
                reponse = requests.get(self.url, timeout=self.timeout)
                reponse.raise_for_status()
                return reponse.json()
            except (requests.Timeout, requests.HTTPError, requests.ConnectionError, requests.RequestException, json.JSONDecodeError) as e:
                derniere_erreur = e
                if getattr(e, "response", None) is not None and e.response.status_code == 429:
                    time.sleep(2 ** tentative)
                else:
                    time.sleep(tentative)
        raise erreur_api(
            f"Échec API {self.url} après {self.tentatives} tentatives"
        ) from derniere_erreur


    def normalise_data(self, lot: pd.DataFrame) -> pd.DataFrame:
        # Mets en forme le retour en fonction du FORMAT, vérifie le cohérence des valeurs et supprime les enregistrements incorrects.
        self._verifie_dataframe_valide(lot)

        correct = (
            lot.assign(
                date=pd.to_datetime(lot["date"], errors="coerce"),
                valeur=pd.to_numeric(lot["valeur"], errors="coerce")
            )
            .dropna(subset=["date", "valeur"])
            .loc[lambda d: d["valeur"].isin([float("inf"), float("-inf")]) == False]
            .assign(ville=self.ville,indicateur=self.nom)
            .reset_index(drop=True)
        )
        return correct[["date", "valeur", "ville", "indicateur"]]

    def _verifie_dataframe_valide(self, lot: pd.DataFrame) -> None:
        manquantes = FORMAT_API - set(lot.columns)
        if manquantes:
            raise erreur_api(
                f"L'extracteur doit produire 'date' et 'valeur', "
                f"reçu : {list(lot.columns)} (manquant : {sorted(manquantes)})"              )


if __name__ == "__main__":

    """ 
    Usage : python module_api.py [--url URL] OR [--latitude F] [--longitude F]
    """

    parseur = argparse.ArgumentParser(description="Interroge l'API Open-Meteo et affiche les températures")
    parseur.add_argument("--latitude", type=float, default=48.85, help="latitude (défaut : Paris)")
    parseur.add_argument("--longitude", type=float, default=2.35, help="longitude (défaut : Paris)")
    parseur.add_argument("--url", default=None, help="URL complète (surclasse latitude/longitude)")
    args = parseur.parse_args()

    url = args.url or (
        f"https://api.open-meteo.com/v1/forecast?latitude={args.latitude}&longitude={args.longitude}&hourly=temperature_2m"
    )

    try:
        from .extracteurs import extracteur_open_meteo   # import local au démo
        source = source_api(url, ville="Paris", nom="temperature",
                            extracteur=extracteur_open_meteo)
        for numerolot, df in enumerate(source.recupere_data()):
            print(f"{'='*60}\n lot {numerolot} — {len(df)} relevés\n{'='*60}")
            print(df.to_string(index=False, max_rows=10))
            print(f"\nMin    : {df['valeur'].min():.1f} °C")
            print(f"Max    : {df['valeur'].max():.1f} °C")
            print(f"Moyenne: {df['valeur'].mean():.1f} °C")
    except erreur_api as erreur:
        print(f" {erreur}", file=sys.stderr)
        sys.exit(1)