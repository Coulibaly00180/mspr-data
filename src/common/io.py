#!/usr/bin/env python3
"""
Module utilitaire pour les opérations d'entrée/sortie robustes.

Ce module fournit des fonctions sécurisées pour la manipulation de fichiers
dans le contexte du projet d'analyse électorale. Il gère notamment :
- L'encoding des fichiers CSV (UTF-8, Latin-1) 
- La création sécurisée de répertoires
- L'écriture robuste avec gestion d'erreurs
- La sélection de colonnes par patterns

Ces utilitaires sont utilisés dans tout le projet pour assurer la robustesse
des opérations I/O, particulièrement importantes lors du traitement
de fichiers CSV provenant de sources diverses (data.gouv.fr, INSEE, etc.)

Auteur: Équipe MSPR Nantes
Date: 2024-2025
"""

import os
import pandas as pd
from typing import List

def ensure_dir(path: str) -> None:
    """
    Crée un répertoire de façon sécurisée s'il n'existe pas déjà.
    
    Cette fonction utilise os.makedirs avec exist_ok=True pour éviter
    les erreurs de concurrence et assurer l'idempotence des opérations.
    
    Args:
        path (str): Chemin du répertoire à créer
        
    Example:
        ensure_dir("/app/reports/trends")  # Crée l'arborescence complète
    """
    os.makedirs(path, exist_ok=True)

def read_csv_safe(path: str, **kwargs) -> pd.DataFrame:
    """
    Lecture robuste de fichiers CSV avec détection automatique d'encoding.
    
    Cette fonction tente plusieurs encodages courants pour maximiser 
    les chances de succès lors du chargement de fichiers CSV français.
    Elle est particulièrement utile avec des données gouvernementales
    qui peuvent utiliser différents encodages selon les sources.
    
    Args:
        path (str): Chemin vers le fichier CSV
        **kwargs: Arguments supplémentaires passés à pd.read_csv()
        
    Returns:
        pd.DataFrame: DataFrame chargé avec l'encoding approprié
        
    Raises:
        Exception: Si tous les encodages échouent
        
    Example:
        df = read_csv_safe("data/elections_2022.csv", sep=";")
    """
    # Essai des encodages les plus courants pour les fichiers français
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    
    # Si tous les encodages échouent, tenter sans spécifier l'encoding
    # (pandas utilisera son détecteur automatique)
    return pd.read_csv(path, **kwargs)

def write_csv_safe(df: pd.DataFrame, path: str, index: bool = False) -> None:
    """
    Écriture sécurisée de DataFrame en CSV avec encoding UTF-8.
    
    Force l'utilisation de l'UTF-8 pour garantir la compatibilité
    et la lisibilité des fichiers de sortie, particulièrement important
    pour les caractères accentués dans les noms de communes françaises.
    
    Args:
        df (pd.DataFrame): DataFrame à sauvegarder
        path (str): Chemin de destination du fichier CSV
        index (bool): Si True, inclut l'index dans le fichier (default: False)
        
    Example:
        write_csv_safe(results_df, "/app/reports/results.csv")
    """
    df.to_csv(path, index=index, encoding="utf-8")

def cols_like(df: pd.DataFrame, prefixes: List[str]) -> List[str]:
    """
    Sélectionne les colonnes d'un DataFrame commençant par certains préfixes.
    
    Fonction utilitaire pour filtrer rapidement les colonnes selon des patterns,
    particulièrement utile pour isoler des groupes de variables (ex: "voix_",
    "pct_", "num_") dans le dataset électoral.
    
    Args:
        df (pd.DataFrame): DataFrame dont on veut filtrer les colonnes
        prefixes (List[str]): Liste des préfixes à rechercher
        
    Returns:
        List[str]: Liste des noms de colonnes correspondant aux préfixes
        
    Example:
        # Sélectionner toutes les colonnes de pourcentages de voix
        vote_cols = cols_like(df, ["voix_pct_", "pct_"])
        
        # Sélectionner les variables numériques preprocessées
        num_cols = cols_like(df, ["num_"])
    """
    return [c for c in df.columns if any(c.startswith(p) for p in prefixes)]
