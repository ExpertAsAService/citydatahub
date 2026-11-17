#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_indicateur.py
Description : Représente une mesure avec métadonnées (nom, unité, catégorie)

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.8
Licence : MIT
Usage :

"""

from dataclasses import dataclass, field

@dataclass
class Indicateur:
    """Un indicateur urbain suivi (ex: température, pollution)."""
    nom: str
    unite: str
    categorie: str = "general"
    seuil_alerte: float | None = None       # None = pas d'alerte

    def __post_init__(self):
        if not self.nom or not self.nom.strip():
            raise ValueError("Le nom d'un indicateur ne peut pas être vide")

    def en_alerte(self, valeur: float) -> bool:
        """Un seuil est-il dépassé pour cette valeur ?"""
        return self.seuil_alerte is not None and valeur > self.seuil_alerte