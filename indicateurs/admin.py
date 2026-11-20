#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : admin.py
Description : Administration des référentiels — le seuil d'alerte se règle
              ici, à chaud, sans SQL ni redémarrage. Mesures et alertes sont
              en lecture seule : elles naissent du pipeline, pas de l'admin.

Auteur : Eric Diologeant
Date : 20 Novembre 2026
Version : 0.1
Licence : MIT
"""

from django.contrib import admin

from .models import Alerte, Categorie, IndicateurRef, Mesure, Source


@admin.register(IndicateurRef)
class IndicateurRefAdmin(admin.ModelAdmin):
    """Le cœur administratif : on règle les seuils, le reste se lit."""
    list_display = ("nom", "unite", "categorie", "seuil_alerte")
    list_filter = ("categorie",)
    search_fields = ("nom",)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("nom",)


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("nom", "type", "url")


@admin.register(Mesure)
class MesureAdmin(admin.ModelAdmin):
    """Lecture seule : le flux vient du pipeline, jamais de l'admin."""
    list_display = ("date", "ville", "indicateur", "valeur")
    list_filter = ("indicateur", "ville")
    date_hierarchy = "date"

    def has_add_permission(self, request):
        return False  # pas de mesure saisie à la main : elle n'aurait pas de source


@admin.register(Alerte)
class AlerteAdmin(admin.ModelAdmin):
    """Lecture seule : les lignes naissent de la détection SQL."""
    list_display = ("date_mesure", "indicateur", "valeur", "seuil")
    list_filter = ("indicateur",)

    def has_add_permission(self, request):
        return False  # une alerte se détecte, elle ne se déclare pas à la main