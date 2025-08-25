#!/usr/bin/env python3
"""
Module d'audit de la qualité des données électorales.

Ce script effectue une analyse critique de la cohérence et de la diversité 
des données électorales de Nantes Métropole. Il détecte notamment :

- Présence des colonnes requises pour l'analyse
- Variation des vainqueurs par commune et élection
- Identification des élections "monochromes" (même vainqueur partout)
- Statistiques de diversité politique territoriale
- Génération de rapports d'audit pour améliorer la qualité des prédictions

Objectif : S'assurer que les données sont suffisamment diversifiées
pour permettre un apprentissage machine efficace.

Usage:
    python src/audit_winner.py
    
Sorties:
    - Rapport console détaillé
    - Fichier CSV d'audit dans reports/checks/
    
Auteur: Équipe MSPR Nantes  
Date: 2024-2025
"""

import pandas as pd
import numpy as np
import os
import sys
from pathlib import Path

def load_dataset():
    """
    Charge le dataset master avec une stratégie de chemins multiples.
    
    Teste plusieurs emplacements possibles pour le fichier master_ml.csv
    afin d'assurer la compatibilité Docker et locale.
    
    Returns:
        pd.DataFrame: Dataset chargé
        
    Raises:
        SystemExit: Si aucun fichier n'est trouvé
    """
    # Chemins possibles pour le fichier master (Docker et local)
    possible_paths = [
        '/app/data/processed_csv/master_ml.csv',  # Chemin Docker
        'data/processed_csv/master_ml.csv',       # Chemin local relatif
        'src/../data/processed_csv/master_ml.csv'  # Chemin alternatif
    ]
    
    for path in possible_paths:
        try:
            df = pd.read_csv(path)
            print(f"✅ Dataset chargé depuis: {path}")
            return df
        except FileNotFoundError:
            continue
    
    print("❌ Erreur: fichier master_ml.csv introuvable dans les emplacements attendus")
    print(f"Chemins testés: {possible_paths}")
    sys.exit(1)

def check_required_columns(df):
    """
    Vérifie la présence des colonnes essentielles pour l'audit.
    
    Args:
        df (pd.DataFrame): Dataset à auditer
        
    Returns:
        bool: True si toutes les colonnes requises sont présentes
    """
    required_cols = [
        'code_commune_insee',  # Identifiant unique de commune
        'annee',              # Année de l'élection  
        'type_scrutin',       # Type d'élection (présidentielle, etc.)
        'tour',               # Tour de scrutin (1 ou 2)
        'parti_en_tete'       # Parti vainqueur dans la commune
    ]
    
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    print('=== AUDIT: Contrôle qualité des données électorales ===\n')
    print('1. 🔍 Vérification de l\'intégrité des colonnes:')
    
    if missing_cols:
        print(f'   ❌ Colonnes manquantes: {missing_cols}')
        print('   ⚠️  Impact: Audit limité par manque de données')
        return False
    else:
        print('   ✅ Toutes les colonnes requises sont présentes')
    
    print(f'   📊 Dimensions du dataset: {df.shape[0]} lignes × {df.shape[1]} colonnes')
    print()
    
    return True

# Chargement principal du dataset
df = load_dataset()

# Vérification de l'intégrité des colonnes
columns_ok = check_required_columns(df)

# 2. Check uniqueness of key combination
key_cols = ['code_commune_insee', 'annee', 'type_scrutin', 'tour']
duplicates = df.duplicated(subset=key_cols).sum()

print('2. Key uniqueness check:')
print(f'   Total rows: {len(df):,}')
print(f'   Unique key combinations: {df[key_cols].drop_duplicates().shape[0]:,}')
print(f'   Number of duplicates: {duplicates}')
if duplicates == 0:
    print('   ✅ No duplicates found')
else:
    print('   ❌ Duplicates detected!')
print()

# 3. Calculate variation statistics per triplet
print('3. Winner variation analysis:')
analysis_cols = ['annee', 'type_scrutin', 'tour']
results = []

for group_key, group_data in df.groupby(analysis_cols):
    annee, type_scrutin, tour = group_key
    
    # Skip rows where parti_en_tete is null/empty
    valid_data = group_data.dropna(subset=['parti_en_tete'])
    valid_data = valid_data[valid_data['parti_en_tete'].astype(str).str.strip() != '']
    
    if len(valid_data) == 0:
        continue
        
    nb_communes = valid_data['code_commune_insee'].nunique()
    nb_vainqueurs = valid_data['parti_en_tete'].nunique()
    monochrome = (nb_vainqueurs == 1 and nb_communes > 1)
    
    results.append({
        'annee': int(annee) if pd.notna(annee) else None,
        'type_scrutin': type_scrutin,
        'tour': int(tour) if pd.notna(tour) else None,
        'nb_communes': nb_communes,
        'nb_vainqueurs': nb_vainqueurs,
        'monochrome': monochrome
    })

# Convert to DataFrame and sort
results_df = pd.DataFrame(results)
results_df = results_df.sort_values(['annee', 'type_scrutin', 'tour'])

print('   Summary table:')
print(results_df.to_string(index=False))
print()

# 4. Find monochrome cases
monochrome_cases = results_df[results_df['monochrome'] == True]

print('4. Monochrome cases analysis:')
if len(monochrome_cases) == 0:
    print('   ✅ No monochrome cases found')
else:
    print(f'   ❌ Found {len(monochrome_cases)} monochrome case(s):')
    for idx, case in monochrome_cases.iterrows():
        print(f'      - {case["annee"]} {case["type_scrutin"]} T{case["tour"]}: {case["nb_communes"]} communes, 1 winner')
        
        # Show sample for first monochrome case
        if idx == monochrome_cases.index[0]:
            print(f'      Sample communes for {case["annee"]} {case["type_scrutin"]} T{case["tour"]}:')
            sample_data = df[(df['annee'] == case['annee']) & 
                           (df['type_scrutin'] == case['type_scrutin']) & 
                           (df['tour'] == case['tour'])][['code_commune_insee', 'nom_commune', 'parti_en_tete']].head(10)
            for _, row in sample_data.iterrows():
                print(f'        {row["code_commune_insee"]} ({row["nom_commune"]}) → {row["parti_en_tete"]}')

print()

# 5. Final verdict
if len(monochrome_cases) == 0:
    print('5. VERDICT FINAL:')
    print('   ✅ OK — variation observed on all combinations')
    print('   Winner calculation appears to be done correctly per commune.')
else:
    print('5. VERDICT FINAL:')
    print('   ❌ PROBLÈME — at least one monochrome election (winner probably propagated)')
    print()
    print('RECOMMENDATION:')
    print('Recalculer le vainqueur dans l\'ETL avec une agrégation par (code_commune_insee, annee, type_scrutin, tour),')
    print('puis refaire la jointure sur cette clé complète avant d\'exporter les cartes.')

# 6. Save results
try:
    os.makedirs('/app/reports/checks', exist_ok=True)
    results_df.to_csv('/app/reports/checks/winner_variation.csv', index=False)
    print(f'\n6. Results saved to: /app/reports/checks/winner_variation.csv')
except:
    try:
        os.makedirs('reports/checks', exist_ok=True)
        results_df.to_csv('reports/checks/winner_variation.csv', index=False)
        print(f'\n6. Results saved to: reports/checks/winner_variation.csv')
    except Exception as e:
        print(f'\n6. Warning: Could not save results file: {e}')