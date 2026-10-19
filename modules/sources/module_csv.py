#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_csv.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.4
Licence : MIT
Usage : 

"""

import sys
import argparse
import pandas as pd

from pathlib import Path
from typing import Iterator
from module_base import source_data

FORMAT_CSV = {"date", "valeur", "ville", "indicateur"}

class erreur_csv(Exception):
    # Erreur levée lors de la validation ou de la lecture d'un fichier CSV.
    pass

class source_csv(source_data):
    # Traitement du fichier csv, fct en mode standard et autonome, test d'erreurs fichier et contenu
    # Sortie selon un format utilisable, nettoyage des lignes incorrecte

    def __init__(self, chemin: str, taille_lot: int = 1000, nom: str = "", description: str = ""):
        self.chemin = Path(chemin)
        self.taille_lot = taille_lot
        self.verifie_file()
        super().__init__(nom=nom or self.chemin.stem, description=description)
    
    def recupere_data(self) -> Iterator[pd.DataFrame]: 
        # Génère les données du CSV lot par lot
        for lot in pd.read_csv(self.chemin, chunksize=self.taille_lot, sep=r"[,;\t]", engine="python"):
            yield self.normalise_data(lot)

    def verifie_file(self) -> None:
        # Vérifie l'existence du fichier et que ce n'est pas un répertoire
        if not self.chemin.exists():
            raise erreur_csv(f"Fichier introuvable : {self.chemin}")
        if not self.chemin.is_file():
            raise erreur_csv(f"Ce n'est pas un fichier : {self.chemin}")
        if self.chemin.stat().st_size == 0:
            raise erreur_csv(f"Fichier de taille 0 : {self.chemin}")

        # Vérifie si c'est bien un csv
        try:
            df = pd.read_csv(self.chemin, chunksize=1, nrows=1, sep=r"[,;\t]", engine="python")
            next(iter(df))
            df.close()
            print("CSV valide - poursuite du traitement : ")
        except StopIteration:
            raise erreur_csv(f"Contenu vide ou séparateur non détecté : {self.chemin}") from None
        except pd.errors.EmptyDataError:
            raise erreur_csv(f"Fichier vide : {self.chemin}") from None
        except pd.errors.ParserError:
            raise erreur_csv(f"Format CSV invalide : {self.chemin}") from None
        except UnicodeDecodeError:
            raise erreur_csv(f"Format non supporté : {self.chemin}") from None

    def normalise_data(self, lot: pd.DataFrame) -> pd.DataFrame:
        # Mets en forme le csv en fonction du FORMAT, vérifie le cohérence des valeurs et supprime les enregistrements incorrects.
        self.verifie_csv_valide(lot)

        correct = (
            lot.assign(
                date=pd.to_datetime(lot["date"], errors="coerce"),
                valeur=pd.to_numeric(lot["valeur"], errors="coerce"),
                ville=lot["ville"].astype("string").str.strip().str.lower(),
                indicateur=lot["indicateur"].astype("string").str.strip(),
            )
            .dropna(subset=["date", "valeur", "ville", "indicateur"])
            .loc[lambda d: d["valeur"].isin([float("inf"), float("-inf")]) == False]
            .reset_index(drop=True)
        )
        return correct[["date", "valeur", "ville", "indicateur"]]

    def verifie_csv_valide(self, lot: pd.DataFrame) -> None:
        manquantes = FORMAT_CSV - set(lot.columns)
        if manquantes:
            raise erreur_csv(f"Colonnes manquantes dans {self.chemin} : {sorted(manquantes)}")

if __name__ == "__main__":

    """ 
    Usage : python module_csv.py --taille-lot N PATH/FICHIER
    Nomfichier: vide.csv, presquevide.csv, monfichiertest.csv, erreurcolonne.csv et erreurdansenregistrement.csv
    """

    parseur = argparse.ArgumentParser(description="Liste un CSV par lots à l'écran")
    parseur.add_argument("fichier", help="chemin du CSV à lire")
    parseur.add_argument("--taille-lot", type=int, default=5, help="optionnel, nombre de lignes par lot (défaut: 5)")
    args = parseur.parse_args()

    try:
        source = source_csv(args.fichier, taille_lot=args.taille_lot)
        for numerolot, lot in enumerate(source.recupere_data()):
            print(f"--- lot {numerolot} : {len(lot)} lignes ---")
            print(lot.to_string(index=False))
    except erreur_csv as erreur:
        print(f"{erreur}", file=sys.stderr)
        sys.exit(1)
