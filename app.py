#!/usr/bin/env python3
"""
Point d'entrée principal pour l'application MSPR Nantes Docker.
Lance l'entraînement des modèles améliorés par défaut.
"""

import sys
import os
import subprocess

def main():
    print("=== MSPR NANTES - ANALYSE ELECTORALE ===")
    print("Lancement de l'entraînement des modèles améliorés...")
    
    try:
        # S'assurer que les répertoires existent
        os.makedirs("/app/data", exist_ok=True)
        os.makedirs("/app/reports", exist_ok=True)
        os.makedirs("/app/reports/figures", exist_ok=True)
        
        # Vérifier la présence des données
        if not os.path.exists("/app/data/processed_csv/master_ml.csv"):
            print("ERREUR: Fichier de données manquant - /app/data/processed_csv/master_ml.csv")
            print("Veuillez monter le volume data correctement.")
            return 1
        
        # Lancer l'entraînement des modèles améliorés
        cmd = [
            "python", "/app/src/models/train_improved.py",
            "--models", "rf", "logreg",
            "--test-years", "2022"
        ]
        
        print(f"Commande: {' '.join(cmd)}")
        result = subprocess.run(cmd, cwd="/app")
        
        if result.returncode == 0:
            print("\n✅ ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS!")
            print("📁 Résultats disponibles dans /app/reports")
            return 0
        else:
            print(f"\n❌ ERREUR lors de l'entraînement (code: {result.returncode})")
            return result.returncode
            
    except Exception as e:
        print(f"❌ ERREUR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())