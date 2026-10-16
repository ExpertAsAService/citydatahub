#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : sourcededonnees.py
Description : Gére la récupération et la normalisation des données

Auteur : Eric Diologeant
Date : 16 Octobre 2026
Version : 0.1
Licence : MIT
Usage : Classe abstraite qui ne peut pas être instanciée directement / modèle pour les imports api et csv

"""

from abc import ABC, abstractmethod
from typing import Iterator

import pandas as pd 

