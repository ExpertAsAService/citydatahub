#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_views.py
Description : test

Auteur : Eric Diologeant
Date : 5 Novembre 2026
Version : 0.1
Licence : MIT
Usage : pytest tests/test_views.py -v

"""

import pytest
from django.test import RequestFactory


def test_accueil_ajoute_indicateur(db):
    from indicateurs.models import Mesure

    Mesure.objects.create(
        date="2026-11-01T10:00+00:00",
        valeur=18.5,
        ville="Paris",
        indicateur="temperature",
        collecte_le="2026-11-01T10:00+00:00",
    )
    from indicateurs.views import accueil

    reponse = accueil(RequestFactory().get("/"))
    assert b"temperature" in reponse.content
