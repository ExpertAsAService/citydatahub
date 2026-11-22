#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : views.py
Description : Vues Django de l'application indicateurs.
              accueil / par_indicateur : lecture de la base.
              collecte : configurateur qui déclenche le pipeline.
              import_csv : upload d'un CSV (cahier des charges RNCP) —
              le site appelle le pipeline, il ne le réécrit pas.

Auteur : Eric Diologeant
Date : 21 Novembre 2026
Version :
Licence : MIT
"""

import os
import tempfile

from django.contrib.auth.decorators import login_required
from django.db import models
from django.shortcuts import render
from django.utils import timezone

from .forms import FormulaireCollecte, FormulaireImport
from .models import Alerte, Import, Mesure


def accueil(request):
    """Page d'accueil : indicateurs disponibles, mesures, badge d'alertes."""
    resume = (
        Mesure.objects.values("indicateur")  # GROUP BY indicateur (SQL !)
        .annotate(nb=models.Count("id"), villes=models.Count("ville", distinct=True))
        .order_by("indicateur")
    )
    alertes_recentes = Alerte.objects.select_related(
        "indicateur", "mesure"
    ).order_by(  # pas de N+1 sur les relations
        "-date_mesure"
    )[
        :5
    ]  # les 5 dernières pour l'écran
    return render(
        request,
        "indicateurs/accueil.html",
        {
            "resume": resume,
            "total_alertes": Alerte.objects.count(),
            "alertes_recentes": alertes_recentes,
        },
    )


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
    """Configurateur : déclenche une collecte à la demande."""
    from modules.sources.fournisseurs import COMBINAISONS, creer_source
    from modules.sources.module_api import erreur_api
    from modules.stockage.stockage_postgres import stockage_postgres, erreur_stockage

    formulaire = FormulaireCollecte(request.POST or None)
    message, erreur = None, None
    if request.method == "POST" and formulaire.is_valid():
        source_nom, ville = formulaire.cleaned_data["combinaison"].split(":", 1)
        try:
            cle = COMBINAISONS[(source_nom, ville)]  # clé réelle du registre
            source = creer_source(cle)
            stockage = stockage_postgres()
            lignes = sum(stockage.insere(lot) for lot in source.recupere_data())
            alertes = (
                stockage.detecte_alertes()
            )  # Suit la collecte, comme le pipeline
            if lignes:
                message = (
                    f"{lignes} nouvelles mesures collectées pour {ville} ({source_nom}) "
                    f"— {alertes} nouvelle(s) alerte(s)."
                )
            else:
                message = "Aucune nouvelle mesure : données déjà à jour."
        except (erreur_api, erreur_stockage) as e:
            erreur = str(e)  # panne affichée à l'écran, pas de crash
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


@login_required
def import_csv(request):
    """Upload d'un CSV — le site APPELLE le pipeline, il ne le réécrit pas :
    source_csv vérifie la structure, stockage insère (idempotence), la
    détection suit l'import, chaque tentative est historisée."""
    from modules.sources import erreur_csv, source_csv
    from modules.stockage.stockage_postgres import erreur_stockage, stockage_postgres

    formulaire = FormulaireImport(request.POST or None, request.FILES or None)
    message, erreur = None, None
    if request.method == "POST" and formulaire.is_valid():
        fichier = formulaire.cleaned_data["fichier"]
        lues, inserees = 0, 0
        # Django streame déjà les gros fichiers vers un temporaire :
        # on l'y écrit proprement, source_csv lira par lots (mémoire constante).
        try:
            with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as temporaire:
                for morceau in fichier.chunks():
                    temporaire.write(morceau)
                chemin = temporaire.name
            try:
                source = source_csv(chemin)  # fail-fast : structure vérifiée là
                stockage = stockage_postgres()
                for lot in source.recupere_data():
                    lues += len(lot)
                    inserees += stockage.insere(lot)
                alertes = stockage.detecte_alertes()
                statut = "succes"
                message = (
                    f"{inserees} mesures importées sur {lues} lues — "
                    f"{alertes} nouvelle(s) alerte(s)."
                )
            finally:
                os.remove(chemin)  # pas de fichier qui traîne
        except (erreur_csv, erreur_stockage) as e:
            statut, erreur = "echec", str(e)  # feedback, jamais de crash
        Import.objects.create(  # monitoring : un essai = une ligne, même en échec
            fichier=fichier.name,
            utilisateur=request.user.username,
            lignes_lues=lues,
            lignes_inserees=inserees,
            lignes_rejetees=max(lues - inserees, 0),
            statut=statut,
            erreur=erreur,
            date_import=timezone.now(),
        )
    return render(
        request,
        "indicateurs/import_csv.html",
        {"form": formulaire, "message": message, "erreur": erreur},
    )
