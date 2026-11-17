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
import sys

from .sources import FOURNISSEURS, creer_source, source_csv, erreur_csv, erreur_api
from .stockage.stockage_postgres import stockage_postgres, erreur_stockage
from modules.journalisation import configure_journal


def execute(
    sources: dict, stockage: stockage_postgres, taille_lot: int = 10_000
) -> dict:
    """Itère les sources, stocke chaque lot, rend le bilan par source."""
    journal = configure_journal()
    bilan = {}
    for cle, fabrique in sources.items():
        source = fabrique()
        collectees, nouvelles, erreur = 0, 0, None
        try:
            for lot in source.recupere_data():
                collectees += len(lot)
                nouvelles += stockage.insere(lot)
        except (erreur_api, erreur_csv, erreur_stockage) as e:
            erreur = str(e)  # on journalise, on NE LÈVE PAS
            journal.warning("source en panne | source=%s | erreur=%s", cle, erreur)
        journal.info(
            "collecte | source=%s | collectees=%s | nouvelles=%s",
            cle,
            collectees,
            nouvelles,
        )
        bilan[cle] = {
            "collectees": collectees,
            "nouvelles": nouvelles,
            "erreur": erreur,
        }
    return bilan


if __name__ == "__main__":
    journal = configure_journal()
    stockage = stockage_postgres()
    sources = {cle: (lambda c=cle: creer_source(c)) for cle in FOURNISSEURS}
    bilan = execute(sources, stockage)

    for cle, etat in bilan.items():
        journal.info(
            "bilan | source=%s | collectees=%s | nouvelles=%s | erreur=%s",
            cle,
            etat["collectees"],
            etat["nouvelles"],
            etat["erreur"],
        )

    echecs = [cle for cle, r in bilan.items() if r["erreur"]]
    sys.exit(1 if echecs else 0)
