#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_api_json.py
Description : test

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.7
Licence : MIT
Usage : pytest tests/test_api_json.py -v

"""

import pytest
from django.test import Client

@pytest.fixture
def client():
    return Client()

@pytest.mark.django_db
class TestApiMesures:
    def test_api_rend_donnees(self, client):
        from indicateurs.models import Mesure
        Mesure.objects.create(
            date="2026-11-17T10:00+00:00", valeur=18.5, ville="Paris",
            indicateur="temperature", collecte_le="2026-11-17T10:00+00:00",
        )
        reponse = client.get("/api/mesures/temperature?ville=Paris")
        assert reponse.status_code == 200
        corps = reponse.json()
        assert corps["indicateur"] == "temperature"
        assert corps["nb"] == 1
        assert corps["mesures"][0]["valeur"] == 18.5

    def test_api_aucune_donnee(self, client):
        reponse = client.get("/api/mesures/temperature")
        assert reponse.status_code == 200
        assert reponse.json()["nb"] == 0

    def test_api_parametre_invalide_400(self, client):
        reponse = client.get("/api/mesures/temperature?jours=abc")
        assert reponse.status_code == 400

    def test_api_hors_bornes_400(self, client):
        reponse = client.get("/api/mesures/temperature?jours=400")
        assert reponse.status_code == 400

    def test_api_post_405(self, client):
        reponse = client.post("/api/mesures/temperature")
        assert reponse.status_code == 405