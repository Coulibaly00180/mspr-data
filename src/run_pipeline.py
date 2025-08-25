#!/usr/bin/env python3
"""
Pipeline principal d'entraînement des modèles électoraux.

Ce script orchestre le processus complet de machine learning :
1. ETL : Construction du dataset maître à partir des données brutes
2. TRAIN : Entraînement des modèles de prédiction électorale

Usage:
    python run_pipeline.py
    
Variables d'environnement:
    TEST_YEARS: Années à utiliser pour le test (par défaut: dernière année)
    
Auteur: Équipe MSPR Nantes
Date: 2024-2025
"""

import os
import shlex
import subprocess
import sys

def main():
    """
    Fonction principale qui exécute le pipeline ML complet.
    
    Le pipeline comprend deux étapes principales :
    1. ETL (Extract, Transform, Load) - Préparation des données
    2. TRAIN - Entraînement des modèles prédictifs
    """
    
    # Lecture de la variable d'environnement TEST_YEARS (années séparées par des espaces)
    # Permet de spécifier quelles années utiliser pour tester les modèles
    test_years = os.environ.get("TEST_YEARS", "").strip()
    
    # Construction de la commande ETL
    # Transforme les données brutes CSV en dataset unifié pour le ML
    etl_cmd = [
        "python", "/app/src/etl/build_master.py",
        "--raw-dir", "/app/data/raw_csv",  # Dossier des données sources
        "--out", "/app/data/processed_csv/master_ml.csv"  # Fichier de sortie unifié
    ]
    
    # Construction de la commande d'entraînement
    # Entraîne plusieurs modèles ML sur les données préparées
    train_cmd = [
        "python", "/app/src/models/train.py",
        "--data", "/app/data/processed_csv/master_ml.csv"
    ]
    
    # Si des années de test sont spécifiées, les ajouter aux arguments
    if test_years:
        train_cmd += ["--test-years", *shlex.split(test_years)]
    
    try:
        # Étape 1: Exécution de l'ETL
        print("[run_pipeline] ETL:", " ".join(etl_cmd), flush=True)
        subprocess.check_call(etl_cmd)
        
        # Étape 2: Entraînement des modèles
        print("[run_pipeline] TRAIN:", " ".join(train_cmd), flush=True)
        subprocess.check_call(train_cmd)
        
        print("[run_pipeline] ✅ Pipeline terminé avec succès !")
        
    except subprocess.CalledProcessError as e:
        print(f"[run_pipeline] ❌ Erreur lors de l'exécution: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[run_pipeline] ❌ Erreur inattendue: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
