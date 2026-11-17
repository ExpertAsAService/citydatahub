#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : urls.py
Description :   Routage des vues et de l'API de l'application indicateurs

Auteur : Eric Diologeant
Date : 6 Novembre 2026
Version : 0.8
Licence : MIT
Usage :

"""

from django.urls import path
from . import views, api

urlpatterns = [
    path("", views.accueil, name="accueil"),
    path("indicateur/<str:indicateur>/", views.par_indicateur, name="par_indicateur"),
    path("collecte/", views.collecte, name="collecte"),
    path("api/mesures/<str:indicateur>", api.api_mesures, name="api_mesures"),
]
