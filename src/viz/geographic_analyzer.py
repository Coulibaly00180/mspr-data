#!/usr/bin/env python3
"""
Analyseur géographique pour les tendances électorales

Génère des cartes choroplèthes et analyses spatiales des résultats électoraux.
Intègre les données GeoJSON des communes de Nantes Métropole.
"""

import argparse
import os
import sys
import json
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import LinearSegmentedColormap, Normalize
import matplotlib.cm as cm
from pathlib import Path

def load_data(data_path, geojson_path):
    """Charge les données électorales et géographiques"""
    print(f"📂 Chargement des données depuis {data_path}")
    
    try:
        df = pd.read_csv(data_path)
    except FileNotFoundError:
        print(f"❌ Fichier de données non trouvé: {data_path}")
        sys.exit(1)
    
    print(f"📍 Chargement du GeoJSON depuis {geojson_path}")
    try:
        with open(geojson_path, 'r', encoding='utf-8') as f:
            geojson_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Fichier GeoJSON non trouvé: {geojson_path}")
        print("💡 Lancez d'abord: docker compose run --rm app python src/etl/fetch_geojson.py")
        sys.exit(1)
    
    # Nettoyage des données
    df['annee'] = pd.to_numeric(df['annee'], errors='coerce')
    df = df.dropna(subset=['annee', 'famille_politique', 'code_commune_insee'])
    df['code_commune_insee'] = df['code_commune_insee'].astype(str).str.zfill(5)
    
    print(f"✅ Données chargées: {len(df)} lignes électorales, {len(geojson_data['features'])} communes GeoJSON")
    return df, geojson_data

def create_party_color_map():
    """Crée une carte de couleurs pour les familles politiques"""
    colors = {
        'PS': '#FF6B9D',      # Rose
        'LR': '#4A90E2',      # Bleu
        'RE': '#F5A623',      # Orange/Jaune
        'LREM': '#F5A623',    # Orange/Jaune (alias RE)
        'RN': '#8B4513',      # Marron foncé
        'FN': '#8B4513',      # Marron foncé (alias RN)
        'LFI': '#D0021B',     # Rouge
        'EELV': '#7ED321',    # Vert
        'MODEM': '#BD10E0',   # Violet
        'PCF': '#D0021B',     # Rouge communiste
        'DVG': '#FF1744',     # Rouge gauche
        'DVD': '#1976D2',     # Bleu droite
        'DIV': '#9E9E9E',     # Gris divers
        'EXG': '#B71C1C',     # Rouge extrême
        'EXD': '#3E2723',     # Marron extrême droite
    }
    return colors

def analyze_geographic_trends(df, output_dir):
    """Analyse des tendances géographiques"""
    print("🗺️  Analyse des tendances géographiques")
    
    # 1. Stabilité/volatilité par commune
    stability_analysis = []
    
    for commune in df['code_commune_insee'].unique():
        commune_data = df[df['code_commune_insee'] == commune]
        
        if len(commune_data) > 1:
            # Calcul de la diversité des partis gagnants
            unique_winners = commune_data['famille_politique'].nunique()
            total_elections = len(commune_data)
            volatility = unique_winners / total_elections
            
            # Parti le plus fréquent
            most_frequent = commune_data['famille_politique'].mode().iloc[0]
            frequency = (commune_data['famille_politique'] == most_frequent).sum() / total_elections
            
            stability_analysis.append({
                'code_commune_insee': commune,
                'nom_commune': commune_data['nom_commune'].iloc[0],
                'volatilite': volatility,
                'parti_dominant': most_frequent,
                'dominance_pct': frequency * 100,
                'nb_elections': total_elections
            })
    
    stability_df = pd.DataFrame(stability_analysis)
    
    # Sauvegarde de l'analyse
    stability_path = os.path.join(output_dir, 'analyse_stabilite_communes.csv')
    stability_df.to_csv(stability_path, index=False)
    
    print(f"📊 Analyse de stabilité sauvegardée: {stability_path}")
    return stability_df

def create_choropleth_map(df, geojson_data, year, scrutin, tour, output_dir):
    """Crée une carte choroplèthe pour une élection donnée"""
    print(f"🗺️  Génération carte: {year} {scrutin} T{tour}")
    
    # Filtrage des données
    election_data = df[
        (df['annee'] == year) & 
        (df['type_scrutin'] == scrutin) & 
        (df['tour'] == tour)
    ].copy()
    
    if election_data.empty:
        print(f"⚠️  Aucune donnée pour {year} {scrutin} T{tour}")
        return None
    
    # Couleurs des partis
    color_map = create_party_color_map()
    
    # Configuration de la figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_aspect('equal')
    ax.axis('off')
    
    # Dictionnaire des données électorales par commune
    election_dict = election_data.set_index('code_commune_insee').to_dict('index')
    
    # Dessiner chaque commune
    legend_parties = set()
    
    for feature in geojson_data['features']:
        code_insee = feature['properties'].get('code', '').zfill(5)
        
        if code_insee in election_dict:
            parti = election_dict[code_insee]['famille_politique']
            color = color_map.get(parti, '#CCCCCC')  # Gris par défaut
            legend_parties.add(parti)
        else:
            color = '#F0F0F0'  # Gris clair pour les communes sans données
            parti = 'Sans données'
        
        # Extraction des coordonnées de la géométrie
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
        elif feature['geometry']['type'] == 'MultiPolygon':
            # Pour les MultiPolygons, prendre le premier polygone
            coords = feature['geometry']['coordinates'][0][0]
        else:
            continue
        
        # Conversion en arrays numpy pour matplotlib
        x_coords = [coord[0] for coord in coords]
        y_coords = [coord[1] for coord in coords]
        
        # Dessiner le polygone
        ax.fill(x_coords, y_coords, color=color, edgecolor='white', linewidth=0.5, alpha=0.8)
        
        # Ajouter le nom de la commune si disponible
        if code_insee in election_dict and len(coords) > 3:
            centroid_x = sum(x_coords) / len(x_coords)
            centroid_y = sum(y_coords) / len(y_coords)
            commune_name = election_dict[code_insee].get('nom_commune', '')
            if len(commune_name) < 15:  # Éviter les noms trop longs
                ax.text(centroid_x, centroid_y, commune_name, 
                       fontsize=6, ha='center', va='center', 
                       bbox=dict(boxstyle="round,pad=0.1", facecolor='white', alpha=0.7))
    
    # Légende
    legend_elements = []
    for parti in sorted(legend_parties):
        color = color_map.get(parti, '#CCCCCC')
        legend_elements.append(mpatches.Patch(color=color, label=parti))
    
    ax.legend(handles=legend_elements, loc='upper left', bbox_to_anchor=(1.02, 1))
    
    # Titre
    ax.set_title(f'Parti en tête par commune - {scrutin.title()} {year} Tour {tour}', 
                fontsize=16, pad=20)
    
    # Ajout d'informations statistiques
    stats_text = f"Communes analysées: {len(election_data)}\n"
    stats_text += f"Participation moyenne: {election_data['turnout_pct'].mean()*100:.1f}%\n"
    party_counts = election_data['famille_politique'].value_counts()
    stats_text += f"Parti dominant: {party_counts.index[0]} ({party_counts.iloc[0]} communes)"
    
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10,
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
           verticalalignment='bottom')
    
    # Sauvegarde
    filename = f'carte_{year}_{scrutin}_t{tour}.png'
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Carte sauvegardée: {filename}")
    return output_path

def create_evolution_comparison(df, geojson_data, output_dir):
    """Crée une comparaison de l'évolution entre plusieurs élections"""
    print("🗺️  Génération: Comparaison évolution")
    
    # Sélection d'élections clés pour comparaison
    key_elections = [
        (2012, 'presidentielle', 1),
        (2017, 'presidentielle', 1),
        (2022, 'presidentielle', 1)
    ]
    
    fig, axes = plt.subplots(1, 3, figsize=(20, 8))
    color_map = create_party_color_map()
    
    for i, (year, scrutin, tour) in enumerate(key_elections):
        ax = axes[i]
        ax.set_aspect('equal')
        ax.axis('off')
        
        # Données de l'élection
        election_data = df[
            (df['annee'] == year) & 
            (df['type_scrutin'] == scrutin) & 
            (df['tour'] == tour)
        ].copy()
        
        if election_data.empty:
            ax.text(0.5, 0.5, f'Pas de données\\n{year} {scrutin}', 
                   ha='center', va='center', transform=ax.transAxes)
            continue
        
        election_dict = election_data.set_index('code_commune_insee').to_dict('index')
        
        # Dessiner les communes
        for feature in geojson_data['features']:
            code_insee = feature['properties'].get('code', '').zfill(5)
            
            if code_insee in election_dict:
                parti = election_dict[code_insee]['famille_politique']
                color = color_map.get(parti, '#CCCCCC')
            else:
                color = '#F0F0F0'
            
            # Géométrie
            if feature['geometry']['type'] == 'Polygon':
                coords = feature['geometry']['coordinates'][0]
            elif feature['geometry']['type'] == 'MultiPolygon':
                coords = feature['geometry']['coordinates'][0][0]
            else:
                continue
            
            x_coords = [coord[0] for coord in coords]
            y_coords = [coord[1] for coord in coords]
            ax.fill(x_coords, y_coords, color=color, edgecolor='white', linewidth=0.3, alpha=0.8)
        
        ax.set_title(f'{scrutin.title()} {year}', fontsize=14)
    
    # Légende commune
    all_parties = set()
    for year, scrutin, tour in key_elections:
        election_data = df[(df['annee'] == year) & (df['type_scrutin'] == scrutin) & (df['tour'] == tour)]
        all_parties.update(election_data['famille_politique'].unique())
    
    legend_elements = [mpatches.Patch(color=color_map.get(parti, '#CCCCCC'), label=parti) 
                      for parti in sorted(all_parties)]
    fig.legend(handles=legend_elements, loc='center', bbox_to_anchor=(0.5, 0.02), ncol=6)
    
    plt.suptitle('Évolution des tendances électorales - Présidentielles T1', fontsize=16, y=0.95)
    plt.tight_layout()
    plt.subplots_adjust(bottom=0.1)
    
    output_path = os.path.join(output_dir, 'evolution_presidentielles_comparison.png')
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return output_path

def create_participation_map(df, geojson_data, year, scrutin, tour, output_dir):
    """Crée une carte de la participation électorale"""
    print(f"🗺️  Génération carte participation: {year} {scrutin} T{tour}")
    
    # Filtrage des données
    election_data = df[
        (df['annee'] == year) & 
        (df['type_scrutin'] == scrutin) & 
        (df['tour'] == tour)
    ].copy()
    
    if election_data.empty or 'turnout_pct' not in election_data.columns:
        print(f"⚠️  Pas de données de participation pour {year} {scrutin} T{tour}")
        return None
    
    # Préparation des données de participation
    participation_data = election_data.dropna(subset=['turnout_pct'])
    if participation_data.empty:
        print("⚠️  Aucune donnée de participation valide")
        return None
    
    # Configuration de la carte de couleurs
    min_participation = participation_data['turnout_pct'].min()
    max_participation = participation_data['turnout_pct'].max()
    norm = Normalize(vmin=min_participation, vmax=max_participation)
    cmap = cm.YlOrRd  # Colormap du jaune au rouge
    
    # Configuration de la figure
    fig, ax = plt.subplots(1, 1, figsize=(14, 10))
    ax.set_aspect('equal')
    ax.axis('off')
    
    participation_dict = participation_data.set_index('code_commune_insee')['turnout_pct'].to_dict()
    
    # Dessiner chaque commune
    for feature in geojson_data['features']:
        code_insee = feature['properties'].get('code', '').zfill(5)
        
        if code_insee in participation_dict:
            participation = participation_dict[code_insee]
            color = cmap(norm(participation))
        else:
            color = '#F0F0F0'  # Gris pour les communes sans données
        
        # Géométrie
        if feature['geometry']['type'] == 'Polygon':
            coords = feature['geometry']['coordinates'][0]
        elif feature['geometry']['type'] == 'MultiPolygon':
            coords = feature['geometry']['coordinates'][0][0]
        else:
            continue
        
        x_coords = [coord[0] for coord in coords]
        y_coords = [coord[1] for coord in coords]
        ax.fill(x_coords, y_coords, color=color, edgecolor='white', linewidth=0.5, alpha=0.8)
    
    # Barre de couleur
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, shrink=0.6, aspect=30)
    cbar.set_label('Taux de participation (%)', rotation=270, labelpad=20)
    
    # Titre et informations
    ax.set_title(f'Taux de participation - {scrutin.title()} {year} Tour {tour}', 
                fontsize=16, pad=20)
    
    stats_text = f"Participation moyenne: {participation_data['turnout_pct'].mean()*100:.1f}%\n"
    stats_text += f"Min: {min_participation*100:.1f}% - Max: {max_participation*100:.1f}%"
    
    ax.text(0.02, 0.02, stats_text, transform=ax.transAxes, fontsize=10,
           bbox=dict(boxstyle="round,pad=0.3", facecolor='white', alpha=0.8),
           verticalalignment='bottom')
    
    # Sauvegarde
    filename = f'participation_{year}_{scrutin}_t{tour}.png'
    output_path = os.path.join(output_dir, filename)
    plt.savefig(output_path, dpi=300, bbox_inches='tight', facecolor='white')
    plt.close()
    
    print(f"✅ Carte de participation sauvegardée: {filename}")
    return output_path

def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(description="Analyse géographique des tendances électorales")
    parser.add_argument("--data", default="/app/data/processed_csv/master_ml.csv",
                       help="Chemin vers le fichier de données")
    parser.add_argument("--geojson", default="/app/data/geo/communes_nantes_metropole.geojson",
                       help="Chemin vers le fichier GeoJSON des communes")
    parser.add_argument("--output", default="/app/reports/geographic",
                       help="Répertoire de sortie pour les cartes")
    parser.add_argument("--year", type=int, help="Année spécifique à analyser")
    parser.add_argument("--scrutin", help="Type de scrutin à analyser")
    parser.add_argument("--tour", type=int, default=1, help="Tour du scrutin")
    parser.add_argument("--all-elections", action="store_true",
                       help="Générer des cartes pour toutes les élections")
    
    args = parser.parse_args()
    
    # Création du répertoire de sortie
    os.makedirs(args.output, exist_ok=True)
    print(f"📁 Répertoire de sortie: {args.output}")
    
    # Chargement des données
    df, geojson_data = load_data(args.data, args.geojson)
    
    # Analyse de stabilité géographique
    analyze_geographic_trends(df, args.output)
    
    output_files = []
    
    if args.all_elections:
        # Génération de cartes pour toutes les élections
        print("🗺️  Génération de toutes les cartes électorales...")
        
        elections = df.groupby(['annee', 'type_scrutin', 'tour']).size().reset_index()
        
        for _, election in elections.iterrows():
            year, scrutin, tour = election['annee'], election['type_scrutin'], election['tour']
            
            # Carte des résultats
            result_map = create_choropleth_map(df, geojson_data, year, scrutin, tour, args.output)
            if result_map:
                output_files.append(result_map)
            
            # Carte de participation
            participation_map = create_participation_map(df, geojson_data, year, scrutin, tour, args.output)
            if participation_map:
                output_files.append(participation_map)
    
    elif args.year and args.scrutin:
        # Génération pour une élection spécifique
        result_map = create_choropleth_map(df, geojson_data, args.year, args.scrutin, args.tour, args.output)
        if result_map:
            output_files.append(result_map)
        
        participation_map = create_participation_map(df, geojson_data, args.year, args.scrutin, args.tour, args.output)
        if participation_map:
            output_files.append(participation_map)
    
    else:
        # Génération de cartes par défaut
        print("🗺️  Génération des cartes par défaut...")
        
        # Comparaison des présidentielles
        evolution_map = create_evolution_comparison(df, geojson_data, args.output)
        if evolution_map:
            output_files.append(evolution_map)
        
        # Dernière élection présidentielle
        latest_presidential = df[df['type_scrutin'] == 'presidentielle']['annee'].max()
        if pd.notna(latest_presidential):
            result_map = create_choropleth_map(df, geojson_data, int(latest_presidential), 'presidentielle', 1, args.output)
            if result_map:
                output_files.append(result_map)
    
    print(f"\n✅ Analyse géographique terminée!")
    print(f"🗺️  {len(output_files)} cartes générées")
    print(f"📁 Fichiers dans: {args.output}")
    
    if output_files:
        print("\n📋 Fichiers générés:")
        for file_path in output_files:
            print(f"  - {os.path.basename(file_path)}")

if __name__ == "__main__":
    main()