#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : journalisation.py
Description :   Collecte les données et gére le processus

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.1
Licence : MIT
Usage :

"""

import logging
import sys

def configure_journal(niveau: str = "INFO") -> logging.Logger:
    journal = logging.getLogger("citydatahub")
    if journal.handlers:            # déjà configuré (imports multiples)
        return journal
    journal.setLevel(niveau)
    sortie = logging.StreamHandler(sys.stdout)
    sortie.setFormatter(logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s"
    ))
    journal.addHandler(sortie)
    return journal