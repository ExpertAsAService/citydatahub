#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_csv.py
Description : Hérite de module_base.py, gère l'import massif de fichiers CSV

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.1
Licence : MIT
Usage : 

"""

import pandas as pd

class source_csv:
    """ Desc """

    def __init__(self, chemin: str, taille_lot: int = 5):
        self.chemin = chemin
        self.taille_lot = taille_lot
    
    def charge_data(self):
        """ Desc """
        for numerolot, lot in enumerate (pd.read_csv(self.chemin, chunksize=self.taille_lot), start=1):
            print(f"--- lot {numerolot} : {len(lot)} lignes ---")
            print(lot.to_string(index=False))

if __name__ == "__main__":
    source = source_csv("/home/ericd/citydatahub/data/monfichiertest.csv")
    source.charge_data()