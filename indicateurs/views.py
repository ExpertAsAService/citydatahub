#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : views.py
Description :   Gère l'import massif de fichiers CSV
                Mode standard, Hérite de la classe abstraite module_base.py
                Mode autonome, peut s'éxécuter directement dans le cadre de test et de développement

Auteur : Eric Diologeant
Date : 6 Novembre 2026
Version : 0.7
Licence : MIT
Usage :

"""

from django.db import models 
from django.shortcuts import render, get_object_or_404

from .models import Mesure


def accueil(request):
    """Page d'accueil : les indicateurs disponibles et le nombre de mesures."""
    resume = (
        Mesure.objects.values("indicateur")       # GROUP BY indicateur (SQL!)
        .annotate(nb=models.Count("id"),
                  villes=models.Count("ville", distinct=True))
        .order_by("indicateur")
    )
    return render(request, "indicateurs/accueil.html", {"resume": resume})


def par_indicateur(request, indicateur: str):
    """Détail : dernières mesures + série pour le graphique, par ville."""
    dernieres = Mesure.objects.filter(indicateur=indicateur)[:50]
    series = (
        Mesure.objects.filter(indicateur=indicateur)
        .order_by("date")
        .values("date", "valeur", "ville")
    )
    return render(request, "indicateurs/detail.html", {
        "indicateur": indicateur,
        "mesures": dernieres,
        "series": list(series),
    })
