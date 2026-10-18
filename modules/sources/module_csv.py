#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_csv.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.2
Licence : MIT
Usage : 

"""

import argparse
import pandas as pd

from pathlib import Path
from typing import Iterator
from module_base import source_data

class source_csv(source_data):
    """ Desc """

    def __init__(self, chemin: str, taille_lot: int = 1000, nom: str = "", description: str = ""):
        self.chemin = Path(chemin)
        self.taille_lot = taille_lot
        super().__init__(nom=nom or self.chemin.stem, description=description)
    
    def recupere_data(self) -> Iterator[pd.DataFrame]: 
        """ Génère les données du CSV lot par lot """
        for lot in pd.read_csv(self.chemin, chunksize=self.taille_lot):
            yield self.normalise_data(lot)

    def normalise_data(self, lot: pd.DataFrame) -> pd.DataFrame:
        """ A implémenter """
        return lot

if __name__ == "__main__":

    """ 
    Usage : python module_csv.py --taille-lot N PATH/FICHIER
    """

    parseur = argparse.ArgumentParser(description="Liste un CSV par lots à l'écran")
    parseur.add_argument("fichier", help="chemin du CSV à lire")
    parseur.add_argument("--taille-lot", type=int, default=5, help="optionnel, nombre de lignes par lot (défaut: 5)")
    args = parseur.parse_args()

    source = source_csv(args.fichier, taille_lot=args.taille_lot)
    
    for numerolot, lot in enumerate(source.recupere_data()):
        print(f"--- lot {numerolot} : {len(lot)} lignes ---")
        print(lot.to_string(index=False))