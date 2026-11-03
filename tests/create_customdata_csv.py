#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : create_customdata_csv.py
Description : Création d'un fichier csv >100Mo avec des données cohérentes

Auteur : Eric Diologeant
Date : 02 Novembre 2026
Version : 08
Licence : MIT
Usage : python tests/create_customdata_csv.py --heures 1000 --sortie data/test.csv

"""

import argparse
import csv
import random
from datetime import datetime, timedelta

# bornes par ville -> données plausibles ET répartition contrôlée
VILLES = {
    "Paris":      {"lat": 48.85, "plage": (-5, 35)},
    "Lyon":       {"lat": 45.75, "plage": (-7, 37)},
    "Marseille":  {"lat": 43.30, "plage": (-3, 40)},
    "Rouen":     {"lat": 49.44, "plage": (-12, 33)},
}
INDICATEURS = ["temperature", "pollution_pm25", "velos_disponibles"]

def genere_mesures(debut: datetime, heures: int):
    for h in range(heures):
        date = debut + timedelta(hours=h)
        # variation saisonnière simple : sinusoïde annuelle + bruit
        saison = 10 * ((h % 24) - 12) / 12
        for ville, conf in VILLES.items():
            mini, maxi = conf["plage"]
            temperature = round(random.uniform(mini, maxi) + saison, 1)
            yield (date.isoformat(), temperature, "temperature", ville)
            pm25 = round(random.uniform(2, 55), 1)
            yield (date.isoformat(), pm25, "pollution_pm25", ville)
            velos = random.randint(0, 60)
            yield (date.isoformat(), velos, "velos_disponibles", ville)


def main() -> None:
    parseur = argparse.ArgumentParser(description="Génère des CSV fictifs massifs.")
    parseur.add_argument("--heures", type=int, default=200_000,
                         help="nombre d'heures simulées (défaut : 200000)")
    parseur.add_argument("--sortie", default="data/mesures_fictives.csv")
    args = parseur.parse_args()

    debut = datetime(2000, 1, 1)
    lignes = 0
    with open(args.sortie, "w", newline="") as f:
        fichier = csv.writer(f)
        fichier.writerow(["date", "valeur", "indicateur", "ville"])
        for ligne in genere_mesures(debut, args.heures):
            fichier.writerow(ligne)
            lignes += 1
    print(f"{lignes:,} lignes écrites -> {args.sortie}")


if __name__ == "__main__":
    main()