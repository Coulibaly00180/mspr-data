#!/usr/bin/env python3
"""
Script de visualisation des tendances électorales - Nantes Métropole

Génère plusieurs types de graphiques pour analyser l'évolution des tendances politiques:
- Évolution temporelle des partis
- Comparaison entre types de scrutin
- Analyse de la participation
- Tendances socio-économiques
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from datetime import datetime
from pathlib import Path

# Configuration matplotlib pour Docker
plt.switch_backend('Agg')  # Backend non-interactif
plt.style.use('default')

def setup_matplotlib():
    """Configure matplotlib pour un rendu optimal"""
    plt.rcParams.update({
        'figure.figsize': [12, 8],
        'font.size': 10,
        'axes.titlesize': 14,
        'axes.labelsize': 12,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.dpi': 150,
        'savefig.dpi': 300,
        'savefig.bbox': 'tight',
        'axes.grid': True,
        'grid.alpha': 0.3
    })

def load_data(filepath):
    """Charge et prépare les données"""
    print(f"Chargement des données depuis {filepath}")
    
    try:
        df = pd.read_csv(filepath)
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filepath}")
        sys.exit(1)
    
    # Conversion des types
    df['annee'] = pd.to_numeric(df['annee'], errors='coerce')
    df['date_scrutin'] = pd.to_datetime(df['date_scrutin'], errors='coerce')
    
    # Nettoyage
    df = df.dropna(subset=['annee', 'famille_politique'])
    df = df[df['famille_politique'].astype(str).str.strip() != '']
    
    print(f"✅ Données chargées: {len(df)} lignes, {len(df.columns)} colonnes")
    print(f"Période: {df['annee'].min():.0f} - {df['annee'].max():.0f}")
    print(f"Types de scrutin: {', '.join(df['type_scrutin'].unique())}")
    
    return df

def plot_party_evolution(df, output_dir):
    """Évolution temporelle des familles politiques"""
    print("📊 Génération: Évolution des familles politiques")
    
    # Agrégation par année et famille politique
    party_counts = df.groupby(['annee', 'famille_politique']).size().unstack(fill_value=0)
    
    # Calcul des pourcentages
    party_pcts = party_counts.div(party_counts.sum(axis=1), axis=0) * 100
    
    # Plot
    plt.figure(figsize=(14, 8))
    
    # Sélection des principales familles politiques
    top_parties = party_pcts.sum().sort_values(ascending=False).head(8).index
    
    for party in top_parties:
        plt.plot(party_pcts.index, party_pcts[party], marker='o', linewidth=2, label=party)
    
    plt.title('Évolution des familles politiques dans la Métropole de Nantes', fontsize=16, pad=20)
    plt.xlabel('Année')
    plt.ylabel('Pourcentage des communes gagnées (%)')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.xticks(party_pcts.index)
    
    output_path = os.path.join(output_dir, 'evolution_familles_politiques.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path

def plot_turnout_evolution(df, output_dir):
    """Évolution de la participation électorale"""
    print("📊 Génération: Évolution de la participation")
    
    # Calcul de la participation moyenne par année et type de scrutin
    turnout_data = df.groupby(['annee', 'type_scrutin'])['turnout_pct'].mean().reset_index()
    
    plt.figure(figsize=(14, 8))
    
    # Plot par type de scrutin
    for scrutin in turnout_data['type_scrutin'].unique():
        data = turnout_data[turnout_data['type_scrutin'] == scrutin]
        plt.plot(data['annee'], data['turnout_pct'] * 100, 
                marker='o', linewidth=2, label=scrutin.title(), markersize=8)
    
    plt.title('Évolution de la participation électorale par type de scrutin', fontsize=16, pad=20)
    plt.xlabel('Année')
    plt.ylabel('Taux de participation (%)')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)
    
    # Ajout des valeurs sur les points
    for scrutin in turnout_data['type_scrutin'].unique():
        data = turnout_data[turnout_data['type_scrutin'] == scrutin]
        for _, row in data.iterrows():
            plt.annotate(f"{row['turnout_pct']*100:.1f}%", 
                        (row['annee'], row['turnout_pct']*100),
                        textcoords="offset points", xytext=(0,10), ha='center')
    
    output_path = os.path.join(output_dir, 'evolution_participation.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path

def plot_scrutin_comparison(df, output_dir):
    """Comparaison des résultats par type de scrutin"""
    print("📊 Génération: Comparaison par type de scrutin")
    
    # Agrégation par type de scrutin et famille politique
    scrutin_data = df.groupby(['type_scrutin', 'famille_politique']).size().unstack(fill_value=0)
    scrutin_pcts = scrutin_data.div(scrutin_data.sum(axis=1), axis=0) * 100
    
    # Sélection des principales familles
    top_parties = scrutin_pcts.sum().sort_values(ascending=False).head(6).index
    scrutin_pcts_filtered = scrutin_pcts[top_parties]
    
    plt.figure(figsize=(14, 8))
    scrutin_pcts_filtered.plot(kind='bar', stacked=False, ax=plt.gca())
    
    plt.title('Répartition des victoires par famille politique et type de scrutin', fontsize=16, pad=20)
    plt.xlabel('Type de scrutin')
    plt.ylabel('Pourcentage des communes gagnées (%)')
    plt.legend(title='Famille politique', bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(rotation=45)
    plt.grid(True, alpha=0.3)
    
    output_path = os.path.join(output_dir, 'comparaison_scrutins.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path

def plot_socioeconomic_trends(df, output_dir):
    """Analyse des tendances socio-économiques"""
    print("📊 Génération: Tendances socio-économiques")
    
    # Vérification des colonnes socio-économiques
    socio_cols = ['population', 'revenu_median_uc_euros', 'taux_chomage_pct', 
                  'taux_pauvrete_pct', 'delinquance_pour_1000_hab']
    available_cols = [col for col in socio_cols if col in df.columns]
    
    if not available_cols:
        print("⚠️  Aucune colonne socio-économique trouvée")
        return None
    
    # Évolution moyenne des indicateurs
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    axes = axes.flatten()
    
    for i, col in enumerate(available_cols[:4]):  # Limite à 4 graphiques
        if i >= 4:
            break
            
        data = df.groupby('annee')[col].mean().dropna()
        if len(data) > 1:
            axes[i].plot(data.index, data.values, marker='o', linewidth=2, markersize=6)
            axes[i].set_title(f'Évolution: {col.replace("_", " ").title()}')
            axes[i].set_xlabel('Année')
            axes[i].grid(True, alpha=0.3)
            
            # Trend line
            z = np.polyfit(data.index, data.values, 1)
            p = np.poly1d(z)
            axes[i].plot(data.index, p(data.index), "r--", alpha=0.7, linewidth=1)
    
    # Masquer les axes non utilisés
    for i in range(len(available_cols), 4):
        axes[i].set_visible(False)
    
    plt.suptitle('Évolution des indicateurs socio-économiques', fontsize=16)
    plt.tight_layout()
    
    output_path = os.path.join(output_dir, 'tendances_socioeconomiques.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path

def plot_correlation_matrix(df, output_dir):
    """Matrice de corrélation des variables numériques"""
    print("📊 Génération: Matrice de corrélation")
    
    # Sélection des variables numériques pertinentes
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    
    # Filtrage des colonnes pertinentes (éviter trop de bruit)
    relevant_cols = [col for col in numeric_cols if any(keyword in col.lower() for keyword in 
                    ['turnout', 'population', 'revenu', 'chomage', 'pauvrete', 'delinquance', 'pct'])]
    
    if len(relevant_cols) < 2:
        print("⚠️  Pas assez de variables numériques pour la corrélation")
        return None
    
    # Calcul de la matrice de corrélation
    corr_matrix = df[relevant_cols].corr()
    
    # Visualisation
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool))  # Masque triangulaire
    
    sns.heatmap(corr_matrix, mask=mask, annot=True, cmap='coolwarm', center=0,
                square=True, linewidths=0.5, cbar_kws={"shrink": 0.8})
    
    plt.title('Matrice de corrélation des variables électorales et socio-économiques', 
              fontsize=14, pad=20)
    plt.xticks(rotation=45, ha='right')
    plt.yticks(rotation=0)
    
    output_path = os.path.join(output_dir, 'matrice_correlation.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    
    return output_path

def generate_summary_report(df, output_files, output_dir):
    """Génère un rapport de synthèse"""
    print("📄 Génération du rapport de synthèse")
    
    summary = {
        'periode_analysee': f"{df['annee'].min():.0f} - {df['annee'].max():.0f}",
        'nb_communes': df['code_commune_insee'].nunique(),
        'nb_elections': len(df),
        'types_scrutin': list(df['type_scrutin'].unique()),
        'principales_familles': list(df['famille_politique'].value_counts().head(5).index),
        'participation_moyenne': f"{df['turnout_pct'].mean()*100:.1f}%",
        'fichiers_generes': [os.path.basename(f) for f in output_files if f]
    }
    
    # Sauvegarde du rapport JSON
    import json
    report_path = os.path.join(output_dir, 'rapport_synthese.json')
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    # Rapport texte lisible
    txt_report_path = os.path.join(output_dir, 'rapport_synthese.txt')
    with open(txt_report_path, 'w', encoding='utf-8') as f:
        f.write("=== RAPPORT D'ANALYSE DES TENDANCES ÉLECTORALES ===\n\n")
        f.write(f"Période analysée: {summary['periode_analysee']}\n")
        f.write(f"Nombre de communes: {summary['nb_communes']}\n")
        f.write(f"Nombre d'élections: {summary['nb_elections']}\n")
        f.write(f"Types de scrutin: {', '.join(summary['types_scrutin'])}\n")
        f.write(f"Participation moyenne: {summary['participation_moyenne']}\n\n")
        f.write("Principales familles politiques:\n")
        for i, famille in enumerate(summary['principales_familles'], 1):
            f.write(f"  {i}. {famille}\n")
        f.write(f"\nFichiers générés: {len(summary['fichiers_generes'])} graphiques\n")
        for fichier in summary['fichiers_generes']:
            f.write(f"  - {fichier}\n")
    
    return txt_report_path

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Analyse des tendances électorales")
    parser.add_argument("--data", default="/app/data/processed_csv/master_ml.csv",
                       help="Chemin vers le fichier de données")
    parser.add_argument("--output", default="/app/reports/trends",
                       help="Répertoire de sortie pour les graphiques")
    parser.add_argument("--types", nargs="*", 
                       choices=["evolution", "participation", "scrutins", "socio", "correlation", "all"],
                       default=["all"], help="Types d'analyses à effectuer")
    
    args = parser.parse_args()
    
    # Configuration
    setup_matplotlib()
    
    # Création du répertoire de sortie
    os.makedirs(args.output, exist_ok=True)
    print(f"📁 Répertoire de sortie: {args.output}")
    
    # Chargement des données
    df = load_data(args.data)
    
    # Génération des visualisations
    output_files = []
    analyses = args.types if "all" not in args.types else ["evolution", "participation", "scrutins", "socio", "correlation"]
    
    if "evolution" in analyses:
        output_files.append(plot_party_evolution(df, args.output))
    
    if "participation" in analyses:
        output_files.append(plot_turnout_evolution(df, args.output))
    
    if "scrutins" in analyses:
        output_files.append(plot_scrutin_comparison(df, args.output))
    
    if "socio" in analyses:
        output_files.append(plot_socioeconomic_trends(df, args.output))
    
    if "correlation" in analyses:
        output_files.append(plot_correlation_matrix(df, args.output))
    
    # Rapport de synthèse
    report_file = generate_summary_report(df, output_files, args.output)
    
    print(f"\n✅ Analyse terminée!")
    print(f"📊 {len([f for f in output_files if f])} graphiques générés")
    print(f"📄 Rapport de synthèse: {os.path.basename(report_file)}")
    print(f"📁 Tous les fichiers dans: {args.output}")

if __name__ == "__main__":
    main()