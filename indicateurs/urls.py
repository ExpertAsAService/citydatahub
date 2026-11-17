#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : urls.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 6 Novembre 2026
Version : 0.7
Licence : MIT
Usage :

"""

from django.urls import path
from . import views

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("indicateur/<str:indicateur>/", views.par_indicateur, name="par_indicateur"),
    path("collecte/", views.collecte, name="collecte"),
]
