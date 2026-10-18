#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_base.py
Description : Gére la récupération et la normalisation des données

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.1
Licence : MIT
Usage : Classe abstraite qui ne peut pas être instanciée directement / modèle pour les imports api et csv.
        Dans les méthodes abstraites, ce sont les sous classes (ici csv, api) qui définissent un format hétérogènes.

"""

from abc import ABC, abstractmethod
from typing import Iterator
import pandas as pd 

class source_data (ABC):
    """ Descripteur appelé à chaque instanciation """
    def __init__(self, nom: str, description: str = ""):
        self.nom = nom
        self.description = description
    

    @abstractmethod
    def recupere_data(self) -> Iterator[pd.DataFrame]:
        """ Récupération des données par l'intermédiaire d'un générateur de lots pour une utilisation mémoire constante """
        ...

    @abstractmethod
    def normalise_data(self, lot: pd.DataFrame) -> pd.DataFrame:
        """ Garantie une mise en forme unique des données avec des types précis """
        ...


