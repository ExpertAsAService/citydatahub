#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_csv.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.1
Licence : MIT
Usage : 

"""
from pathlib import Path
import pandas as pd
import argparse

class source_csv:
    """ Desc """

    def __init__(self, chemin: str, taille_lot: int = 10, nom: str = "",description: str = ""):
        self.chemin = Path(chemin)
        self.taille_lot = taille_lot
    
    def charge_data(self):
        """ Desc """
        for numerolot, lot in enumerate (pd.read_csv(self.chemin, chunksize=self.taille_lot), start=1):
            print(f"--- lot {numerolot} : {len(lot)} lignes ---")
            print(lot.to_string(index=False))

if __name__ == "__main__":
    parseur = argparse.ArgumentParser(description="Liste un CSV par lots à l'écran")
    parseur.add_argument("fichier", help="chemin du CSV à lire")
    args = parseur.parse_args()
    source = source_csv(args.fichier)
    source.charge_data()