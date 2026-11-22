#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : stockage_postgres.py
Description :   Gère l'interface avec la base de données

Auteur : Eric Diologeant
Date : 20 Novembre 2026
Version : 0.6
Licence : MIT
Usage :

"""

import os
from pathlib import Path

from dotenv import load_dotenv

import pandas as pd
import psycopg2
from psycopg2 import extras
from sqlalchemy import create_engine

# Charge les variables d'environnement depuis .env
load_dotenv()


class erreur_stockage(Exception):
    """Erreur métier levée pour tout problème de persistance."""


class stockage_postgres:
    """Insère des lots de mesures dans la table `mesures`."""

    def __init__(self, base: str = None, schema: str = "mesures"):
        # Identifiants par variables d'ENVIRONNEMENT — jamais dans le code
        # (même règle que les futures clés d'API : configuration, pas code)
        self.base = base if base is not None else os.environ.get("PGDATABASE", "citydatahub")
        self.utilisateur = os.environ.get("PGUSER")
        self.mot_de_passe = os.environ.get("PGPASSWORD")
        self.schema = schema
        self.insere_lignes = 0
        try:
            # Si pas de mot de passe, utiliser le socket Unix (authentification peer)
            if self.mot_de_passe:
                self.moteur = create_engine(
                    f"postgresql+psycopg2://{self.utilisateur}:{self.mot_de_passe}@/{self.base}"
                )
            else:
                # Connexion via socket Unix sans mot de passe (peer auth)
                self.moteur = create_engine(
                    f"postgresql+psycopg2://{self.utilisateur}@/{self.base}"
                )
        except Exception as e:
            raise erreur_stockage(f"Connexion impossible : {self.base}") from e

    def insere(self, lot: pd.DataFrame) -> int:
        """Insère un lot (format commun), rend le nombre de lignes écrites."""
        colonnes = {"date", "valeur", "ville", "indicateur"}
        if not colonnes.issubset(lot.columns):
            raise erreur_stockage(
                f"Lot non conforme, colonnes attendues : {sorted(colonnes)}"
            )
        try:
            lignes_ecrites = lot.to_sql(
                self.schema,
                self.moteur,
                if_exists="append",
                index=False,
                method=psycopg2_method_insert_par_lots,
            )
            self.insere_lignes += int(lignes_ecrites)
            return int(lignes_ecrites)
        except Exception as e:
            raise erreur_stockage(f"Échec d'insertion : {e}") from e

    def detecte_alertes(self) -> int:
        """Joue sql/alertes.sql (référence unique) après un import.

        Rend le nombre d'alertes CRÉÉES. Idempotent : UNIQUE(mesure_id)
        + ON CONFLICT DO NOTHING — le rejeu ne peut pas dupliquer.
        """
        chemin = Path(__file__).resolve().parents[2] / "sql" / "alertes.sql"
        try:
            with self.moteur.raw_connection() as connexion:  # connexion DBAPI (psycopg2)
                with connexion.cursor() as curseur:
                    curseur.execute(chemin.read_text())
                    creees = curseur.rowcount
                connexion.commit()  # le commit psycopg2, au bon étage cette fois
            return int(creees)
        except Exception as e:
            raise erreur_stockage(f"Échec de la détection d'alertes : {e}") from e


def psycopg2_method_insert_par_lots(table, conn, keys, data_iter):
    requete = (
        f"INSERT INTO {table.name} ({', '.join(keys)}) VALUES %s "
        "ON CONFLICT (ville, indicateur, date) DO NOTHING "
        "RETURNING date"
    )
    lignes = list(data_iter)
    with conn.connection.cursor() as curseur:
        resultats = extras.execute_values(
            curseur, requete, lignes, page_size=1000, fetch=True
        )
    return len(resultats)
