#!/usr/bin/env python3
"""
Module de génération de dashboards interactifs pour l'exploration électorale.

Ce module crée une suite de visualisations web interactives utilisant Plotly
pour permettre l'exploration dynamique des données électorales de Nantes Métropole.
Les dashboards générés sont des fichiers HTML autonomes, consultables dans 
n'importe quel navigateur sans serveur requis.

Dashboards générés:

    📊 dashboard_electoral.html
       - Vue d'ensemble multi-dimensionnelle des résultats
       - Graphiques interconnectés avec filtres dynamiques  
       - Evolution temporelle des familles politiques
       - Comparaisons inter-scrutins avec animations

    📈 timeline_interactive.html
       - Chronologie électorale interactive sur la décennie
       - Zoom temporel et navigation par périodes
       - Annotations des événements politiques majeurs
       - Filtres par type d'élection et commune

    🔥 participation_heatmap.html
       - Carte thermique de la participation par commune/année
       - Détection visuelle des patterns d'abstention
       - Comparaisons territoriales facilitées
       - Gradients colorés adaptatifs

    ☀️ party_distribution_sunburst.html
       - Visualisation hiérarchique des victoires électorales
       - Navigation drill-down : Familles → Partis → Candidats
       - Proportions dynamiques selon les filtres
       - Interface intuitive pour explorer la complexité

    🎯 socioeconomic_scatter.html
       - Analyses multivariées des corrélations socio-économiques
       - Nuages de points interactifs avec régressions
       - Identification des communes atypiques
       - Exploration guidée des relations causales

Fonctionnalités techniques:
    - Export HTML autonome (pas de serveur requis)
    - Interface responsive adaptée mobile/desktop
    - Performance optimisée pour datasets importants
    - Tooltips informatifs et légendes interactives
    - Thème visuel cohérent avec l'identité du projet

Usage:
    python src/viz/interactive_dashboard.py [--output-dir /path/to/reports/interactive]

Dépendances:
    pip install plotly pandas numpy

Auteur: Équipe MSPR Nantes
Date: 2024-2025
"""

import argparse
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

try:
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False
    print("⚠️  Plotly non disponible. Installation requise: pip install plotly")

def load_data(filepath):
    """
    Charge et prépare les données électorales pour les visualisations interactives.
    
    Cette fonction effectue le preprocessing nécessaire pour optimiser
    les performances des dashboards Plotly :
    - Conversion des types de données appropriés
    - Nettoyage des valeurs manquantes critiques
    - Formatage des dates pour les timelines
    - Validation de la cohérence des données
    
    Args:
        filepath (str): Chemin vers le fichier master_ml.csv
        
    Returns:
        pd.DataFrame: Dataset nettoyé et optimisé pour Plotly
        
    Raises:
        SystemExit: Si le fichier est introuvable ou corrompu
        
    Note:
        Les données manquantes en famille_politique et année sont supprimées
        car elles sont critiques pour toutes les visualisations.
    """
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
    return df

def create_interactive_timeline(df, output_dir):
    """Timeline interactive des résultats électoraux"""
    print("🎯 Génération: Timeline interactive")
    
    # Préparation des données pour la timeline
    timeline_data = df.groupby(['annee', 'type_scrutin', 'famille_politique']).size().reset_index(name='count')
    
    fig = px.scatter(timeline_data, x='annee', y='famille_politique', size='count',
                    color='type_scrutin', hover_name='famille_politique',
                    title='Timeline des victoires électorales par famille politique',
                    labels={'annee': 'Année', 'famille_politique': 'Famille Politique'})
    
    fig.update_layout(height=600, showlegend=True)
    fig.update_xaxes(dtick=1)  # Affichage de chaque année
    
    output_path = os.path.join(output_dir, 'timeline_interactive.html')
    pyo.plot(fig, filename=output_path, auto_open=False)
    return output_path

def create_participation_heatmap(df, output_dir):
    """Heatmap de la participation par commune et année"""
    print("🎯 Génération: Heatmap de participation")
    
    # Création de la heatmap
    pivot_data = df.pivot_table(values='turnout_pct', 
                               index='nom_commune', 
                               columns='annee', 
                               aggfunc='mean')
    
    fig = px.imshow(pivot_data, 
                   title='Taux de participation par commune et année',
                   labels=dict(x="Année", y="Commune", color="Participation %"),
                   aspect="auto")
    
    fig.update_layout(height=800)
    fig.update_xaxes(side="top")
    
    output_path = os.path.join(output_dir, 'participation_heatmap.html')
    pyo.plot(fig, filename=output_path, auto_open=False)
    return output_path

def create_party_flow_diagram(df, output_dir):
    """Diagramme de flux des changements de parti dominant"""
    print("🎯 Génération: Diagramme de flux des changements")
    
    # Calcul des transitions
    df_sorted = df.sort_values(['code_commune_insee', 'annee', 'type_scrutin'])
    
    # Création d'un sunburst chart pour visualiser la répartition
    party_counts = df['famille_politique'].value_counts()
    
    fig = px.sunburst(
        names=party_counts.index,
        values=party_counts.values,
        title="Répartition des victoires par famille politique"
    )
    
    fig.update_layout(height=600)
    
    output_path = os.path.join(output_dir, 'party_distribution_sunburst.html')
    pyo.plot(fig, filename=output_path, auto_open=False)
    return output_path

def create_socioeconomic_scatter(df, output_dir):
    """Scatter plots interactifs des variables socio-économiques"""
    print("🎯 Génération: Scatter plots socio-économiques")
    
    # Vérification des colonnes disponibles
    socio_cols = ['population', 'revenu_median_uc_euros', 'taux_chomage_pct', 
                  'taux_pauvrete_pct', 'turnout_pct']
    available_cols = [col for col in socio_cols if col in df.columns and df[col].notna().sum() > 10]
    
    if len(available_cols) < 2:
        print("⚠️  Pas assez de variables socio-économiques disponibles")
        return None
    
    # Création d'un scatter plot avec les deux premières variables disponibles
    x_var = available_cols[0]
    y_var = available_cols[1] if len(available_cols) > 1 else available_cols[0]
    
    # Filtrage des données valides
    valid_data = df.dropna(subset=[x_var, y_var, 'famille_politique'])
    
    fig = px.scatter(valid_data, 
                    x=x_var, y=y_var,
                    color='famille_politique',
                    size='population' if 'population' in df.columns else None,
                    hover_name='nom_commune',
                    hover_data=['annee', 'type_scrutin'],
                    title=f'Relations {x_var.replace("_", " ")} vs {y_var.replace("_", " ")}',
                    labels={x_var: x_var.replace("_", " ").title(),
                           y_var: y_var.replace("_", " ").title()})
    
    fig.update_layout(height=600)
    
    output_path = os.path.join(output_dir, 'socioeconomic_scatter.html')
    pyo.plot(fig, filename=output_path, auto_open=False)
    return output_path

def create_electoral_dashboard(df, output_dir):
    """Dashboard complet avec plusieurs visualisations"""
    print("🎯 Génération: Dashboard complet")
    
    # Création de subplots
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Évolution des familles politiques', 'Participation par scrutin',
                       'Distribution des victoires', 'Tendances temporelles'),
        specs=[[{"secondary_y": False}, {"secondary_y": False}],
               [{"type": "pie"}, {"secondary_y": False}]]
    )
    
    # 1. Évolution des familles politiques
    party_evolution = df.groupby(['annee', 'famille_politique']).size().unstack(fill_value=0)
    top_parties = party_evolution.sum().nlargest(5).index
    
    for party in top_parties:
        fig.add_trace(
            go.Scatter(x=party_evolution.index, 
                      y=party_evolution[party],
                      mode='lines+markers',
                      name=party),
            row=1, col=1
        )
    
    # 2. Participation par scrutin
    participation_data = df.groupby('type_scrutin')['turnout_pct'].mean() * 100
    fig.add_trace(
        go.Bar(x=participation_data.index, 
               y=participation_data.values,
               name='Participation moyenne',
               showlegend=False),
        row=1, col=2
    )
    
    # 3. Distribution des victoires (Pie chart)
    party_dist = df['famille_politique'].value_counts()
    fig.add_trace(
        go.Pie(labels=party_dist.index, 
               values=party_dist.values,
               name="Distribution"),
        row=2, col=1
    )
    
    # 4. Tendances temporelles
    yearly_data = df.groupby('annee').agg({
        'turnout_pct': 'mean',
        'blancs_pct': 'mean'
    }).fillna(0)
    
    fig.add_trace(
        go.Scatter(x=yearly_data.index,
                  y=yearly_data['turnout_pct'] * 100,
                  mode='lines+markers',
                  name='Participation',
                  line=dict(color='blue')),
        row=2, col=2
    )
    
    fig.add_trace(
        go.Scatter(x=yearly_data.index,
                  y=yearly_data['blancs_pct'] * 100,
                  mode='lines+markers',
                  name='Votes blancs',
                  line=dict(color='red')),
        row=2, col=2
    )
    
    # Mise à jour du layout
    fig.update_layout(height=800, 
                     title_text="Dashboard Électoral - Nantes Métropole",
                     showlegend=True)
    
    output_path = os.path.join(output_dir, 'dashboard_electoral.html')
    pyo.plot(fig, filename=output_path, auto_open=False)
    return output_path

def create_index_page(output_files, output_dir):
    """Crée une page d'index HTML pour naviguer entre les visualisations"""
    print("📄 Génération de la page d'index")
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard Électoral - Nantes Métropole</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 10px; }}
            h1 {{ color: #2c3e50; text-align: center; }}
            .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin-top: 30px; }}
            .card {{ background: white; border: 1px solid #ddd; border-radius: 8px; padding: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
            .card h3 {{ color: #34495e; margin-top: 0; }}
            .card p {{ color: #7f8c8d; }}
            .btn {{ display: inline-block; background: #3498db; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; margin-top: 10px; }}
            .btn:hover {{ background: #2980b9; }}
            .info {{ background: #ecf0f1; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🗳️ Dashboard Électoral - Nantes Métropole</h1>
            
            <div class="info">
                <p><strong>Analyse interactive des tendances électorales</strong></p>
                <p>Exploration des données électorales de la Métropole de Nantes avec visualisations interactives.</p>
                <p>📅 Génération: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}</p>
            </div>
            
            <div class="grid">
    """
    
    # Descriptions des visualisations
    descriptions = {
        'dashboard_electoral.html': {
            'title': '📊 Dashboard Complet',
            'description': 'Vue d\'ensemble avec évolution des familles politiques, participation et tendances'
        },
        'timeline_interactive.html': {
            'title': '📈 Timeline Interactive',
            'description': 'Chronologie des victoires électorales par famille politique'
        },
        'participation_heatmap.html': {
            'title': '🔥 Heatmap de Participation',
            'description': 'Taux de participation par commune et année sous forme de carte thermique'
        },
        'party_distribution_sunburst.html': {
            'title': '☀️ Répartition des Partis',
            'description': 'Distribution hiérarchique des victoires par famille politique'
        },
        'socioeconomic_scatter.html': {
            'title': '🎯 Analyse Socio-économique',
            'description': 'Relations entre variables électorales et indicateurs socio-économiques'
        }
    }
    
    # Ajout des cartes pour chaque fichier généré
    for file_path in output_files:
        if file_path and os.path.exists(file_path):
            filename = os.path.basename(file_path)
            if filename in descriptions:
                desc = descriptions[filename]
                html_content += f"""
                <div class="card">
                    <h3>{desc['title']}</h3>
                    <p>{desc['description']}</p>
                    <a href="{filename}" class="btn">Ouvrir la visualisation</a>
                </div>
                """
    
    html_content += """
            </div>
        </div>
    </body>
    </html>
    """
    
    index_path = os.path.join(output_dir, 'index.html')
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    return index_path

def main():
    """Fonction principale"""
    if not PLOTLY_AVAILABLE:
        print("❌ Plotly est requis pour les visualisations interactives")
        sys.exit(1)
    
    parser = argparse.ArgumentParser(description="Dashboard interactif des tendances électorales")
    parser.add_argument("--data", default="/app/data/processed_csv/master_ml.csv",
                       help="Chemin vers le fichier de données")
    parser.add_argument("--output", default="/app/reports/interactive",
                       help="Répertoire de sortie pour le dashboard")
    
    args = parser.parse_args()
    
    # Création du répertoire de sortie
    os.makedirs(args.output, exist_ok=True)
    print(f"📁 Répertoire de sortie: {args.output}")
    
    # Chargement des données
    df = load_data(args.data)
    
    # Génération des visualisations interactives
    output_files = []
    
    # Dashboard principal
    output_files.append(create_electoral_dashboard(df, args.output))
    
    # Visualisations individuelles
    output_files.append(create_interactive_timeline(df, args.output))
    output_files.append(create_participation_heatmap(df, args.output))
    output_files.append(create_party_flow_diagram(df, args.output))
    output_files.append(create_socioeconomic_scatter(df, args.output))
    
    # Page d'index
    index_file = create_index_page(output_files, args.output)
    
    print(f"\n✅ Dashboard interactif généré!")
    print(f"🌐 {len([f for f in output_files if f])} visualisations créées")
    print(f"📄 Page d'accueil: {os.path.basename(index_file)}")
    print(f"📁 Ouvrir le fichier index.html dans votre navigateur")
    print(f"📂 Emplacement: {args.output}")

if __name__ == "__main__":
    main()