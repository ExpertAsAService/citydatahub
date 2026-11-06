#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Nom du script : stockage_postgres.py
Description :   Gère l'imterface  avec la base de données

Auteur : Eric Diologeant
Date : 3 Novembre 2026
Version : 0.1
Licence : MIT
Usage :

"""

import os
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
        self.base = os.environ.get("PGDATABASE", base)
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


def psycopg2_method_insert_par_lots(table, conn, keys, data_iter):
    """Méthode to_sql : INSERT multiplicité (execute_values) au lieu du
    row-by-row — des dizaines de fois plus rapide sur de gros volumes."""
    requete = f"INSERT INTO {table.name} ({', '.join(keys)}) VALUES %s"
    lignes = [ligne for ligne in data_iter]  # itérateur -> liste de tuples
    with conn.connection.cursor() as curseur:
        extras.execute_values(curseur, requete, lignes, page_size=1000)
    return len(lignes)
