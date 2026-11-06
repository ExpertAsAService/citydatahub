#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : pipeline.py
Description :   Collecte les données et gére le processus

Auteur : Eric Diologeant
Date : 3 Novembre 2026
Version : 0.4
Licence : MIT
Usage :

"""

from .sources import FOURNISSEURS, creer_source, source_csv, erreur_csv, erreur_api
from .stockage.stockage_postgres import stockage_postgres, erreur_stockage


def execute(
    sources: dict, stockage: stockage_postgres, taille_lot: int = 10_000
) -> dict:
    """Itère les sources, stocke chaque lot, rend le bilan par source."""
    bilan = {}
    for cle, fabrique in sources.items():
        source = fabrique()
        lignes, erreur = 0, None
        try:
            for lot in source.recupere_data():
                lignes += stockage.insere(lot)
        except (erreur_api, erreur_csv, erreur_stockage) as e:
            erreur = str(e)  # on journalise, on NE LÈVE PAS
        bilan[cle] = {"lignes": lignes, "erreur": erreur}
        print(
            f"[{cle}] {lignes} lignes stockées"
            + (f" | ⚠ {erreur}" if erreur else " | OK")
        )
    return bilan


if __name__ == "__main__":
    import sys

    stockage = stockage_postgres()
    sources = {cle: (lambda c=cle: creer_source(c)) for cle in FOURNISSEURS}
    # + les sources CSV : {"fictif": lambda: source_csv("data/mesures_fictives.csv",
    #                                                    taille_lot=50_000)}
    bilan = execute(sources, stockage)
    echecs = [cle for cle, r in bilan.items() if r["erreur"]]
    sys.exit(1 if echecs else 0)
