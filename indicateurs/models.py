#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : models.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 6 Novembre 2026
Version : 0.5
Licence : MIT
Usage :

"""

from django.db import models


class Mesure(models.Model):
    id = models.BigAutoField(primary_key=True)
    date = models.DateTimeField()
    valeur = models.FloatField()
    ville = models.TextField()
    indicateur = models.TextField()
    collecte_le = models.DateTimeField()

    class Meta:
        managed = False
        db_table = "mesures"
        indexes = []
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"{self.ville} · {self.indicateur} = {self.valeur} ({self.date:%d/%m %Hh})"