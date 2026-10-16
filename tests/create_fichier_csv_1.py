#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : create_fichier_csv_1.py
Description : Création d'un fichier csv de test très basique

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 1.0
Licence : MIT
Usage : python tests/create_fichier_csv.py

"""

import csv
from datetime import datetime, timedelta

with open("data/monfichiertest.csv", "w", newline="") as f:
    fichier = csv.writer(f)
    fichier.writerow(["date", "valeur", "indicateur"])    # en-tête
    for i in range(100):                                    # 10 lignes
        date = datetime(2026, 10, 1) + timedelta(hours=i)
        fichier.writerow([date, 20 + i, "temperature"])   # 20, 21, 22...

print("data/monfichiertest.csv créé")