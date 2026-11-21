#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : forms.py
Description : Formulaire du configurateur de collecte.
              Les choix dérivent de COMBINAISONS (fournisseurs.py) :
              le formulaire ne peut pas proposer une source inexistante.

Auteur : Eric Diologeant
Date : 16 Novembre 2026
Version : 0.6
Licence : MIT
"""

from django import forms

from modules.sources.fournisseurs import COMBINAISONS


class FormulaireCollecte(forms.Form):
    """Un seul champ : le couple (source, ville), issu du registre réel."""

    combinaison = forms.ChoiceField(
        choices=[
            (f"{source}:{ville}", f"{source.replace('_', ' ')} — {ville}")
            for (source, ville) in COMBINAISONS
        ],
        label="Source à collecter",
    )

class FormulaireImport(forms.Form):
    """Un seul champ : le fichier CSV au format commun (4 colonnes)."""
    fichier = forms.FileField(label="Fichier CSV (date, valeur, indicateur, ville)")