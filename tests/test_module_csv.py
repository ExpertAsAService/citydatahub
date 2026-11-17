#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : test_module_csv.py
Description : test

Auteur : Eric Diologeant
Date : 23 Octobre 2026
Version : 0.3
Licence : MIT
Usage : pytest tests/test_module_csv.py -v

"""
import pandas as pd
import pytest

from modules.sources.module_csv import erreur_csv, source_csv


class TestSourceCsv:
    def test_fichier_inexistant(self):
        with pytest.raises(erreur_csv, match="introuvable"):
            source_csv("/chemin/qui/nexiste/pas.csv")

    def test_fichier_vide(self, csv_vide):
        with pytest.raises(erreur_csv, match="taille 0"):
            source_csv(str(csv_vide))

    def test_colonnes_manquantes(self, csv_mauvais_format):
        source = source_csv(str(csv_mauvais_format))
        with pytest.raises(erreur_csv, match="Colonnes manquantes"):
            next(source.recupere_data())

    def test_lignes_invalides_ecartees(self, csv_valide):
        """Les lignes 'pas-un-nombre' et vides doivent être écartées."""
        source = source_csv(str(csv_valide))
        lot = next(source.recupere_data())
        assert len(lot) == 3  # 5 lignes - 2 invalides

    def test_traitement_par_lots(self, csv_valide):
        """chunksize=2 sur 5 lignes valides -> plusieurs lots."""
        source = source_csv(str(csv_valide), taille_lot=2)
        lots = list(source.recupere_data())
        assert len(lots) >= 2

    def test_ville_conservee(self, csv_valide):
        """La colonne ville fait partie du format commun et est conservée."""
        source = source_csv(str(csv_valide))
        lot = next(source.recupere_data())
        assert "ville" in lot.columns
        assert set(lot["ville"]) == {"Paris", "Lyon", "Rouen"}
