#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : views.py
Description : Vues Django de l'application indicateurs.
              accueil / par_indicateur : lecture de la base.
              collecte : configurateur qui déclenche le pipeline S2-S3.

Auteur : Eric Diologeant
Date : 16 Novembre 2026
Version : 0.8
Licence : MIT
"""

from django.db import models
from django.shortcuts import render

from .models import Mesure


def accueil(request):
    """Page d'accueil : les indicateurs disponibles et le nombre de mesures."""
    resume = (
        Mesure.objects.values("indicateur")  # GROUP BY indicateur (SQL!)
        .annotate(nb=models.Count("id"), villes=models.Count("ville", distinct=True))
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
    return render(
        request,
        "indicateurs/detail.html",
        {
            "indicateur": indicateur,
            "mesures": dernieres,
            "series": list(series),
        },
    )


def collecte(request):
    """Configurateur : déclenche une collecte à la demande (pipeline S2-S3)."""
    from modules.sources.fournisseurs import COMBINAISONS, creer_source
    from modules.stockage.stockage_postgres import stockage_postgres, erreur_stockage
    from modules.sources.module_api import erreur_api
    from .forms import FormulaireCollecte

    formulaire = FormulaireCollecte(request.POST or None)
    message, erreur = None, None
    if request.method == "POST" and formulaire.is_valid():
        source_nom, ville = formulaire.cleaned_data["combinaison"].split(":", 1)
        try:
            cle = COMBINAISONS[(source_nom, ville)]  # clé réelle du registre
            source = creer_source(cle)
            stockage = stockage_postgres()
            lignes = sum(stockage.insere(lot) for lot in source.recupere_data())
            message = (
                f"{lignes} nouvelles mesures collectées pour {ville} ({source_nom})."
                if lignes
                else "Aucune nouvelle mesure : données déjà à jour."
            )
        except (erreur_api, erreur_stockage) as e:
            erreur = str(e)  # panne journalisée à l'écran, pas de crash
        except KeyError:
            erreur = "Cette source n'est pas disponible."
    return render(
        request,
        "indicateurs/collecte.html",
        {
            "form": formulaire,
            "message": message,
            "erreur": erreur,
        },
    )
