#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : module_analyseur.py
Description : Calcul tendances, moyennes, pics, agrégations

Auteur : Eric Diologeant
Date : 17 Novembre 2026
Version : 0.8
Licence : MIT
Usage :

"""

import numpy as np
import pandas as pd
from scipy import stats


class AnalyseurDeDonnees:
    """Analyse une série de mesures (date, valeur) d'un indicateur."""

    def __init__(self, mesures: pd.DataFrame):
        if not {"date", "valeur"}.issubset(mesures.columns):
            raise ValueError("Le DataFrame doit contenir 'date' et 'valeur'")
        self.df = mesures.sort_values("date").reset_index(drop=True)

    # ── Statistiques descriptives ──────────────────────────────
    def resume(self) -> dict:
        """min, max, moyenne, écart-type, médiane."""
        v = self.df["valeur"]
        return {
            "nombre": int(len(v)),
            "min": float(v.min()),
            "max": float(v.max()),
            "moyenne": float(v.mean()),
            "mediane": float(v.median()),
            "ecart_type": float(v.std()),
        }

    # ── Tendances ───────────────────────────────────────────────
    def moyenne_mobile(self, fenetre: int = 7) -> pd.Series:
        """Lissage : moyenne glissante sur `fenetre` points."""
        return self.df["valeur"].rolling(window=fenetre).mean()

    def detecter_tendance(self, fenetre: int = 7) -> float:
        """Pente de régression linéaire sur la moyenne mobile.

        > 0 : hausse ; < 0 : baisse ; ~ 0 : stable.
        """
        mm = self.moyenne_mobile(fenetre).dropna()
        if len(mm) < 2:
            return 0.0
        pente, _, _, _, _ = stats.linregress(np.arange(len(mm)), mm.values)
        return float(pente)

    # ── Alertes ─────────────────────────────────────────────────
    def generer_alertes(self, seuil: float) -> pd.DataFrame:
        """Mesures dépassant le seuil, triées par valeur décroissante."""
        depassements = self.df[self.df["valeur"] > seuil].copy()
        return depassements.sort_values("valeur", ascending=False)

    def rapport_alerte(self, seuil: float) -> dict:
        """Synthèse exploitable par le futur module Django."""
        alertes = self.generer_alertes(seuil)
        return {
            "seuil": seuil,
            "nombre": len(alertes),
            "max": float(alertes["valeur"].max()) if len(alertes) else None,
            "premiere_date": str(alertes["date"].iloc[0]) if len(alertes) else None,
        }
