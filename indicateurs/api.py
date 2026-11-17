#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : api.py
Description : Fournir les mesures

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.4
Licence : MIT
"""

from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
@require_GET
def api_mesures(request, indicateur: str):
    """GET /api/mesures/<indicateur>?ville=Paris&jours=7 -> JSON."""
    from .models import Mesure
    from datetime import timedelta
    from django.utils import timezone

    villes = request.GET.getlist("ville")
    try:
        jours = int(request.GET.get("jours", 7))
    except ValueError:
        return JsonResponse(
            {"erreur": "jours doit être un entier"},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )
    if not 1 <= jours <= 365:
        return JsonResponse(
            {"erreur": "jours doit être entre 1 et 365"},
            status=400,
            json_dumps_params={"ensure_ascii": False},
        )

    debut = timezone.now() - timedelta(days=jours)
    requete = Mesure.objects.filter(indicateur=indicateur, date__gte=debut)
    if villes:
        requete = requete.filter(ville__in=villes)
    donnees = [
        {"date": m.date.isoformat(), "ville": m.ville, "valeur": m.valeur}
        for m in requete.order_by("date")[:5000]
    ]
    return JsonResponse(
        {"indicateur": indicateur, "nb": len(donnees), "mesures": donnees}
    )
