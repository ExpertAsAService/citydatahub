#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : create_fichier_csv_1.py
Description : Création d'un fichier csv de test très basique

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 1.1
Licence : MIT
Usage : python tests/create_fichier_csv_1.py

"""

import csv
import random
from datetime import datetime, timedelta

with open("/home/ericd/citydatahub/data/monfichiertest.csv", "w", newline="") as f:
    fichier = csv.writer(f)
    fichier.writerow(["date", "valeur", "ville", "indicateur"])  # en-tête
    for i in range(52):  # 10 lignes
        date = datetime(2026, 10, 1) + timedelta(hours=i)
        ville = random.choice(["paris", "rouen", "marseille"])
        valeur = round(random.uniform(-30, 30), 1)
        fichier.writerow([date, valeur, ville, "temperature"])  # -20 to ...

print("data/monfichiertest.csv créé")
