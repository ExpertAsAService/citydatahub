#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_views.py
Description : Tests des vues Django : pages, formulaire, pannes gérées.

Auteur : Eric Diologeant
Date : 5 Novembre 2026
Version : 0.8
Licence : MIT
Usage : pytest tests/test_views.py -v

"""

from unittest.mock import MagicMock

import pytest
from django.test import Client

from modules.sources.module_api import erreur_api


@pytest.fixture
def client():
    return Client()


@pytest.mark.django_db
class TestPages:
    def test_accueil_ajoute_indicateur(self, client):
        """Le résumé de l'accueil affiche les indicateurs de la base."""
        from indicateurs.models import Mesure

        Mesure.objects.create(
            date="2026-11-17T10:00+00:00",
            valeur=18.5,
            ville="Paris",
            indicateur="temperature",
            collecte_le="2026-11-17T10:00+00:00",
        )
        reponse = client.get("/")
        assert reponse.status_code == 200
        assert b"temperature" in reponse.content

    def test_par_indicateur_affiche_ville(self, client):
        from indicateurs.models import Mesure

        Mesure.objects.create(
            date="2026-11-17T10:00+00:00",
            valeur=18.5,
            ville="Paris",
            indicateur="temperature",
            collecte_le="2026-11-17T10:00+00:00",
        )
        reponse = client.get("/indicateur/temperature/")
        assert reponse.status_code == 200
        assert b"Paris" in reponse.content

    def test_par_indicateur_vide(self, client):
        """Un indicateur sans données rend une page, pas une erreur."""
        reponse = client.get("/indicateur/inconnu/")
        assert reponse.status_code == 200


class TestConfigurateur:
    def test_get_affiche_formulaire(self, client):
        reponse = client.get("/collecte/")
        assert reponse.status_code == 200
        assert b"<form" in reponse.content

    def test_panne_source_affiche_message(self, client, monkeypatch):
        """Source en panne : la page revient AVEC le message, sans exception."""
        from modules.sources.fournisseurs import COMBINAISONS
        import modules.sources.fournisseurs as module_fournisseurs

        source_nom, ville = next(iter(COMBINAISONS))

        def faux_creer_source(cle):
            source = MagicMock()
            source.recupere_data.side_effect = erreur_api("Échec API simulé")
            return source

        monkeypatch.setattr(module_fournisseurs, "creer_source", faux_creer_source)
        reponse = client.post("/collecte/", {"combinaison": f"{source_nom}:{ville}"})
        assert reponse.status_code == 200
        assert b"Erreur" in reponse.content  # le bloc rouge du template
        assert b"simul" in reponse.content  # l'erreur simulée rendue
