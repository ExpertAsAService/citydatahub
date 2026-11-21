#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : models.py
Description : Miroirs ORM des 5 tables CityDataHub (mesures S3 + référentiels
              S6) — sq/schema.sql reste LA référence ; Django ne migre rien
              (managed=False) depuis la S4.

Auteur : Eric Diologeant
Date : 20 Novembre 2026
Version : 0.8
Licence : MIT
"""

from django.db import models


class Mesure(models.Model):
    """Miroir ORM de la table mesures — une ligne = une mesure."""

    id = models.BigAutoField(primary_key=True)
    date = models.DateTimeField()
    valeur = models.FloatField()
    ville = models.TextField()
    indicateur = models.TextField()
    collecte_le = models.DateTimeField()

    class Meta:
        managed = False  # le SQL est la référence, Django ne migre pas
        db_table = "mesures"

    def __str__(self) -> str:
        return f"{self.ville} — {self.indicateur} : {self.valeur} ({self.date:%d/%m %Hh})"


class Categorie(models.Model):
    """Référentiel des catégories (environnement, mobilite, equipements)."""

    id = models.BigAutoField(primary_key=True)
    nom = models.TextField()

    class Meta:
        managed = False
        db_table = "categories"
        ordering = ["nom"]

    def __str__(self) -> str:
        return self.nom


class IndicateurRef(models.Model):
    """Référentiel des indicateurs — la dataclass Indicateur (S2) en table."""

    id = models.BigAutoField(primary_key=True)
    nom = models.TextField()
    unite = models.TextField()
    categorie = models.ForeignKey(
        Categorie, on_delete=models.DO_NOTHING, db_column="categorie_id"
    )
    seuil_alerte = models.FloatField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "indicateurs"
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.unite})"


class Source(models.Model):
    """Miroir en base du registre fournisseurs.py."""

    id = models.BigAutoField(primary_key=True)
    nom = models.TextField()
    type = models.TextField()
    description = models.TextField(blank=True)
    url = models.TextField(blank=True)

    class Meta:
        managed = False
        db_table = "sources"
        ordering = ["nom"]

    def __str__(self) -> str:
        return f"{self.nom} ({self.type})"


class Alerte(models.Model):
    """Dépassement de seuil détecté — une ligne par mesure en excès."""

    id = models.BigAutoField(primary_key=True)
    mesure = models.ForeignKey(
        "Mesure", on_delete=models.DO_NOTHING, db_column="mesure_id"
    )
    indicateur = models.ForeignKey(
        IndicateurRef, on_delete=models.DO_NOTHING, db_column="indicateur_id"
    )
    seuil = models.FloatField()
    valeur = models.FloatField()
    date_mesure = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "alertes"
        ordering = ["-date_mesure"]

    def __str__(self) -> str:
        return f"{self.valeur} > {self.seuil} ({self.date_mesure:%d/%m %Hh})"

class Import(models.Model):
    """Historique des imports CSV lancés depuis le site (monitoring)."""
    fichier = models.TextField()
    utilisateur = models.TextField(null=True)
    lignes_lues = models.IntegerField(default=0)
    lignes_inserees = models.IntegerField(default=0)
    lignes_rejetees = models.IntegerField(default=0)
    statut = models.TextField()
    erreur = models.TextField(null=True)
    date_import = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "imports"
        ordering = ["-date_import"]