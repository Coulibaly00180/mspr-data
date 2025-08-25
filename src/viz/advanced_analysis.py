#!/usr/bin/env python3
"""
Module d'analyse avancée pour générer des graphiques supplémentaires
basés sur les données électorales de Nantes Métropole
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def setup_matplotlib():
    """Configuration de matplotlib pour de beaux graphiques"""
    plt.style.use('seaborn-v0_8')
    plt.rcParams['figure.figsize'] = (12, 8)
    plt.rcParams['font.size'] = 10
    plt.rcParams['axes.titlesize'] = 14
    plt.rcParams['axes.labelsize'] = 12

def load_data():
    """Charge les données depuis le CSV master"""
    data_path = Path('/app/data/processed_csv/master_ml.csv')
    df = pd.read_csv(data_path)
    print(f"Données chargées: {len(df)} lignes, {len(df.columns)} colonnes")
    return df

def analyze_voter_behavior(df, output_dir):
    """
    1. Analyse du comportement électoral : abstention vs participation
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Evolution de l'abstention par type de scrutin
    abstention_by_election = df.groupby(['annee', 'type_scrutin'])['turnout_pct'].mean().reset_index()
    abstention_by_election['abstention_pct'] = 1 - abstention_by_election['turnout_pct']
    
    for scrutin in abstention_by_election['type_scrutin'].unique():
        data_scrutin = abstention_by_election[abstention_by_election['type_scrutin'] == scrutin]
        axes[0,0].plot(data_scrutin['annee'], data_scrutin['abstention_pct']*100, 
                       marker='o', label=scrutin.title(), linewidth=2)
    
    axes[0,0].set_title('Évolution de l\'Abstention par Type de Scrutin (2012-2022)', fontweight='bold')
    axes[0,0].set_xlabel('Année')
    axes[0,0].set_ylabel('Taux d\'Abstention (%)')
    axes[0,0].legend()
    axes[0,0].grid(True, alpha=0.3)
    
    # Corrélation abstention vs revenus
    df_clean = df.dropna(subset=['turnout_pct', 'revenu_median_uc_euros'])
    axes[0,1].scatter(df_clean['revenu_median_uc_euros'], df_clean['turnout_pct']*100, 
                     alpha=0.6, s=50, c='blue')
    z = np.polyfit(df_clean['revenu_median_uc_euros'], df_clean['turnout_pct']*100, 1)
    p = np.poly1d(z)
    axes[0,1].plot(df_clean['revenu_median_uc_euros'], p(df_clean['revenu_median_uc_euros']), 
                   "r--", alpha=0.8, linewidth=2)
    axes[0,1].set_title('Participation vs Revenu Médian', fontweight='bold')
    axes[0,1].set_xlabel('Revenu Médian (€)')
    axes[0,1].set_ylabel('Taux de Participation (%)')
    axes[0,1].grid(True, alpha=0.3)
    
    # Distribution des votes blancs/nuls
    df_valid = df.dropna(subset=['blancs_pct', 'nuls_pct'])
    axes[1,0].hist(df_valid['blancs_pct']*100, bins=30, alpha=0.7, label='Votes Blancs', color='lightblue')
    axes[1,0].hist(df_valid['nuls_pct']*100, bins=30, alpha=0.7, label='Votes Nuls', color='orange')
    axes[1,0].set_title('Distribution des Votes Blancs et Nuls', fontweight='bold')
    axes[1,0].set_xlabel('Pourcentage (%)')
    axes[1,0].set_ylabel('Fréquence')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # Evolution blancs/nuls dans le temps
    blancs_nuls_time = df.groupby('annee')[['blancs_pct', 'nuls_pct']].mean()
    axes[1,1].plot(blancs_nuls_time.index, blancs_nuls_time['blancs_pct']*100, 
                   marker='s', label='Votes Blancs', linewidth=2, color='lightblue')
    axes[1,1].plot(blancs_nuls_time.index, blancs_nuls_time['nuls_pct']*100, 
                   marker='o', label='Votes Nuls', linewidth=2, color='orange')
    axes[1,1].set_title('Évolution des Votes Blancs/Nuls (2012-2022)', fontweight='bold')
    axes[1,1].set_xlabel('Année')
    axes[1,1].set_ylabel('Pourcentage (%)')
    axes[1,1].legend()
    axes[1,1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / 'analyse_comportement_electeur.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Graphique sauvegardé: {output_path}")

def analyze_socioeconomic_impact(df, output_dir):
    """
    2. Impact des facteurs socio-économiques sur le vote
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Variables socio-économiques disponibles
    socio_vars = ['revenu_median_uc_euros', 'taux_chomage_pct', 'taux_pauvrete_pct', 
                  'delinquance_pour_1000_hab', 'population', 'population_delta']
    
    # Corrélations avec participation
    df_clean = df.dropna(subset=socio_vars + ['turnout_pct'])
    
    for i, var in enumerate(socio_vars):
        row = i // 3
        col = i % 3
        
        axes[row, col].scatter(df_clean[var], df_clean['turnout_pct']*100, 
                              alpha=0.6, s=30)
        
        # Ligne de tendance
        z = np.polyfit(df_clean[var], df_clean['turnout_pct']*100, 1)
        p = np.poly1d(z)
        axes[row, col].plot(df_clean[var], p(df_clean[var]), "r--", alpha=0.8)
        
        # Calcul corrélation
        corr = df_clean[var].corr(df_clean['turnout_pct'])
        
        axes[row, col].set_title(f'{var.replace("_", " ").title()}\n(Corrélation: {corr:.3f})', 
                                fontweight='bold')
        axes[row, col].set_xlabel(var.replace('_', ' ').title())
        axes[row, col].set_ylabel('Participation (%)')
        axes[row, col].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / 'impact_socioeconomique.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Graphique sauvegardé: {output_path}")

def analyze_political_volatility(df, output_dir):
    """
    3. Analyse de la volatilité politique par commune
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Changements de winner entre élections
    winner_changes = []
    for commune in df['nom_commune'].unique():
        df_commune = df[df['nom_commune'] == commune].sort_values('annee')
        changes = 0
        for i in range(1, len(df_commune)):
            if (df_commune.iloc[i]['parti_en_tete'] != df_commune.iloc[i-1]['parti_en_tete'] and 
                pd.notna(df_commune.iloc[i]['parti_en_tete']) and 
                pd.notna(df_commune.iloc[i-1]['parti_en_tete'])):
                changes += 1
        winner_changes.append({'commune': commune, 'changes': changes, 
                              'elections': len(df_commune)})
    
    volatility_df = pd.DataFrame(winner_changes)
    volatility_df['volatility_rate'] = volatility_df['changes'] / volatility_df['elections']
    
    # Graphique de volatilité par commune
    axes[0,0].barh(range(len(volatility_df)), volatility_df['volatility_rate'], 
                   color='skyblue', alpha=0.8)
    axes[0,0].set_yticks(range(len(volatility_df)))
    axes[0,0].set_yticklabels(volatility_df['commune'], fontsize=8)
    axes[0,0].set_title('Taux de Volatilité Politique par Commune', fontweight='bold')
    axes[0,0].set_xlabel('Taux de Changement de Vainqueur')
    axes[0,0].grid(True, alpha=0.3, axis='x')
    
    # Distribution de la volatilité
    axes[0,1].hist(volatility_df['volatility_rate'], bins=15, alpha=0.7, color='lightgreen', 
                   edgecolor='black')
    axes[0,1].set_title('Distribution de la Volatilité Politique', fontweight='bold')
    axes[0,1].set_xlabel('Taux de Volatilité')
    axes[0,1].set_ylabel('Nombre de Communes')
    axes[0,1].grid(True, alpha=0.3)
    
    # Evolution du nombre de partis différents par élection
    parties_per_election = df.groupby(['annee', 'type_scrutin'])['parti_en_tete'].nunique().reset_index()
    
    for scrutin in parties_per_election['type_scrutin'].unique():
        data_scrutin = parties_per_election[parties_per_election['type_scrutin'] == scrutin]
        axes[1,0].plot(data_scrutin['annee'], data_scrutin['parti_en_tete'], 
                       marker='o', label=scrutin.title(), linewidth=2)
    
    axes[1,0].set_title('Diversité Politique par Type d\'Élection', fontweight='bold')
    axes[1,0].set_xlabel('Année')
    axes[1,0].set_ylabel('Nombre de Partis Vainqueurs Différents')
    axes[1,0].legend()
    axes[1,0].grid(True, alpha=0.3)
    
    # Simplifier : juste compter les changements de parti par commune dans le temps
    commune_changes = []
    for commune in df['nom_commune'].unique():
        df_commune = df[df['nom_commune'] == commune].sort_values('annee')
        parties = df_commune['famille_politique'].dropna().tolist()
        changes = len(set(parties)) - 1 if len(set(parties)) > 1 else 0
        commune_changes.append({'commune': commune, 'nb_parties': len(set(parties))})
    
    changes_df = pd.DataFrame(commune_changes)
    axes[1,1].barh(range(len(changes_df)), changes_df['nb_parties'], color='lightcoral', alpha=0.8)
    axes[1,1].set_yticks(range(len(changes_df)))
    axes[1,1].set_yticklabels(changes_df['commune'], fontsize=8)
    axes[1,1].set_title('Diversité des Vainqueurs par Commune', fontweight='bold')
    axes[1,1].set_xlabel('Nombre de Familles Politiques Différentes')
    axes[1,1].grid(True, alpha=0.3, axis='x')
    
    plt.tight_layout()
    output_path = output_dir / 'volatilite_politique.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Graphique sauvegardé: {output_path}")

def analyze_candidate_performance(df, output_dir):
    """
    4. Performance des candidats/partis spécifiques dans le temps
    """
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    
    # Evolution des grands candidats présidentiels
    presidential_df = df[df['type_scrutin'] == 'presidentielle'].copy()
    
    if not presidential_df.empty:
        # Candidats majeurs par année
        candidate_cols = ['voix_pct_macron', 'voix_pct_lepen', 'voix_pct_melenchon', 
                         'voix_pct_fillon', 'voix_pct_hollande', 'voix_pct_sarkozy']
        
        for col in candidate_cols:
            if col in presidential_df.columns:
                yearly_avg = presidential_df.groupby('annee')[col].mean()
                yearly_avg = yearly_avg.dropna()
                if not yearly_avg.empty:
                    candidate_name = col.split('_')[-1].title()
                    axes[0,0].plot(yearly_avg.index, yearly_avg*100, 
                                  marker='o', label=candidate_name, linewidth=2)
        
        axes[0,0].set_title('Évolution des Candidats Présidentiels Majeurs', fontweight='bold')
        axes[0,0].set_xlabel('Année')
        axes[0,0].set_ylabel('Score Moyen (%)')
        axes[0,0].legend()
        axes[0,0].grid(True, alpha=0.3)
    
    # Evolution des familles politiques toutes élections confondues
    family_evolution = df.groupby(['annee', 'famille_politique']).size().unstack(fill_value=0)
    family_evolution_pct = family_evolution.div(family_evolution.sum(axis=1), axis=0) * 100
    
    for family in family_evolution_pct.columns[:5]:  # Top 5 familles
        axes[0,1].plot(family_evolution_pct.index, family_evolution_pct[family], 
                       marker='s', label=family, linewidth=2)
    
    axes[0,1].set_title('Évolution des Familles Politiques (% des Victoires)', fontweight='bold')
    axes[0,1].set_xlabel('Année')
    axes[0,1].set_ylabel('Pourcentage des Victoires (%)')
    axes[0,1].legend()
    axes[0,1].grid(True, alpha=0.3)
    
    # Performance par type d'élection
    performance_by_type = df.groupby(['type_scrutin', 'famille_politique']).size().unstack(fill_value=0)
    performance_by_type_pct = performance_by_type.div(performance_by_type.sum(axis=1), axis=0) * 100
    
    performance_by_type_pct.plot(kind='bar', ax=axes[1,0], stacked=True, colormap='Set3')
    axes[1,0].set_title('Répartition des Familles par Type d\'Élection', fontweight='bold')
    axes[1,0].set_xlabel('Type de Scrutin')
    axes[1,0].set_ylabel('Pourcentage (%)')
    axes[1,0].legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    axes[1,0].tick_params(axis='x', rotation=45)
    
    # Scores moyens des partis par commune (heatmap)
    # Prendre les principales formations
    main_parties = ['ps_pct', 'lr_pct', 'rn_pct', 'lrem_pct', 'eelv_pct']
    party_scores = df.groupby('nom_commune')[main_parties].mean()
    
    # Nettoyer les NaN
    party_scores = party_scores.fillna(0)
    
    sns.heatmap(party_scores, annot=False, cmap='RdYlBu_r', ax=axes[1,1], 
                cbar_kws={'label': 'Score Moyen (%)'})
    axes[1,1].set_title('Scores Moyens des Partis par Commune', fontweight='bold')
    axes[1,1].set_xlabel('Partis Politiques')
    axes[1,1].set_ylabel('Communes')
    axes[1,1].tick_params(axis='y', labelsize=8)
    
    plt.tight_layout()
    output_path = output_dir / 'performance_candidats.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Graphique sauvegardé: {output_path}")

def analyze_demographic_patterns(df, output_dir):
    """
    5. Patterns démographiques et géographiques
    """
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # Taille de commune vs participation
    df_clean = df.dropna(subset=['population', 'turnout_pct'])
    
    # Créer des catégories de taille
    df_clean['taille_commune'] = pd.cut(df_clean['population'], 
                                       bins=[0, 10000, 30000, 100000, float('inf')],
                                       labels=['Petite', 'Moyenne', 'Grande', 'Très Grande'])
    
    df_clean.boxplot(column='turnout_pct', by='taille_commune', ax=axes[0,0])
    axes[0,0].set_title('Participation par Taille de Commune')
    axes[0,0].set_xlabel('Taille de Commune')
    axes[0,0].set_ylabel('Taux de Participation')
    axes[0,0].tick_params(axis='x', rotation=45)
    
    # Evolution démographique vs comportement électoral
    df_demo = df.dropna(subset=['population_delta', 'turnout_pct'])
    axes[0,1].scatter(df_demo['population_delta'], df_demo['turnout_pct']*100, alpha=0.6)
    z = np.polyfit(df_demo['population_delta'], df_demo['turnout_pct']*100, 1)
    p = np.poly1d(z)
    axes[0,1].plot(df_demo['population_delta'], p(df_demo['population_delta']), "r--", alpha=0.8)
    axes[0,1].set_title('Évolution Démographique vs Participation')
    axes[0,1].set_xlabel('Variation de Population')
    axes[0,1].set_ylabel('Taux de Participation (%)')
    axes[0,1].grid(True, alpha=0.3)
    
    # Revenus vs choix politiques
    df_revenue = df.dropna(subset=['revenu_median_uc_euros', 'famille_politique'])
    revenue_by_family = df_revenue.groupby('famille_politique')['revenu_median_uc_euros'].mean().sort_values(ascending=False)
    
    axes[0,2].barh(range(len(revenue_by_family)), revenue_by_family.values, color='gold', alpha=0.8)
    axes[0,2].set_yticks(range(len(revenue_by_family)))
    axes[0,2].set_yticklabels(revenue_by_family.index)
    axes[0,2].set_title('Revenu Médian par Famille Politique')
    axes[0,2].set_xlabel('Revenu Médian (€)')
    axes[0,2].grid(True, alpha=0.3, axis='x')
    
    # Chômage vs vote protestataire (RN + LFI)
    df['vote_protestataire'] = df['rn_pct'].fillna(0) + df['lfi_pct'].fillna(0)
    df_protest = df.dropna(subset=['taux_chomage_pct', 'vote_protestataire'])
    
    axes[1,0].scatter(df_protest['taux_chomage_pct'], df_protest['vote_protestataire']*100, 
                     alpha=0.6, color='red')
    z = np.polyfit(df_protest['taux_chomage_pct'], df_protest['vote_protestataire']*100, 1)
    p = np.poly1d(z)
    axes[1,0].plot(df_protest['taux_chomage_pct'], p(df_protest['taux_chomage_pct']), 
                   "black", linewidth=2)
    axes[1,0].set_title('Chômage vs Vote Protestataire (RN+LFI)')
    axes[1,0].set_xlabel('Taux de Chômage (%)')
    axes[1,0].set_ylabel('Vote Protestataire (%)')
    axes[1,0].grid(True, alpha=0.3)
    
    # Délinquance vs participation
    df_delin = df.dropna(subset=['delinquance_pour_1000_hab', 'turnout_pct'])
    axes[1,1].scatter(df_delin['delinquance_pour_1000_hab'], df_delin['turnout_pct']*100,
                     alpha=0.6, color='purple')
    z = np.polyfit(df_delin['delinquance_pour_1000_hab'], df_delin['turnout_pct']*100, 1)
    p = np.poly1d(z)
    axes[1,1].plot(df_delin['delinquance_pour_1000_hab'], p(df_delin['delinquance_pour_1000_hab']), 
                   "r--", alpha=0.8)
    axes[1,1].set_title('Délinquance vs Participation')
    axes[1,1].set_xlabel('Délinquance pour 1000 hab')
    axes[1,1].set_ylabel('Taux de Participation (%)')
    axes[1,1].grid(True, alpha=0.3)
    
    # Associations actives vs vote écologique
    df_asso = df.dropna(subset=['associations_actives', 'eelv_pct'])
    axes[1,2].scatter(df_asso['associations_actives'], df_asso['eelv_pct']*100,
                     alpha=0.6, color='green')
    z = np.polyfit(df_asso['associations_actives'], df_asso['eelv_pct']*100, 1)
    p = np.poly1d(z)
    axes[1,2].plot(df_asso['associations_actives'], p(df_asso['associations_actives']), 
                   "darkgreen", linewidth=2)
    axes[1,2].set_title('Associations vs Vote Écologique')
    axes[1,2].set_xlabel('Nombre d\'Associations Actives')
    axes[1,2].set_ylabel('Score EELV (%)')
    axes[1,2].grid(True, alpha=0.3)
    
    plt.tight_layout()
    output_path = output_dir / 'patterns_demographiques.png'
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"✓ Graphique sauvegardé: {output_path}")

def generate_summary_report(df, output_dir):
    """Génère un rapport de synthèse des nouvelles analyses"""
    
    total_elections = len(df)
    total_communes = df['nom_commune'].nunique()
    years_span = f"{df['annee'].min()}-{df['annee'].max()}"
    avg_participation = df['turnout_pct'].mean() * 100
    
    # Calcul de statistiques avancées
    volatility_stats = []
    for commune in df['nom_commune'].unique():
        df_commune = df[df['nom_commune'] == commune].sort_values('annee')
        changes = 0
        for i in range(1, len(df_commune)):
            if (df_commune.iloc[i]['parti_en_tete'] != df_commune.iloc[i-1]['parti_en_tete'] and 
                pd.notna(df_commune.iloc[i]['parti_en_tete']) and 
                pd.notna(df_commune.iloc[i-1]['parti_en_tete'])):
                changes += 1
        if len(df_commune) > 0:
            volatility_stats.append(changes / len(df_commune))
    
    avg_volatility = np.mean(volatility_stats) if volatility_stats else 0
    
    # Corrélations importantes
    corr_participation_revenu = df['turnout_pct'].corr(df['revenu_median_uc_euros'])
    corr_chomage_protestataire = df['taux_chomage_pct'].corr(
        df['rn_pct'].fillna(0) + df['lfi_pct'].fillna(0)
    )
    
    report_content = f"""=== RAPPORT D'ANALYSES AVANCÉES ===

Période analysée: {years_span}
Nombre total d'élections: {total_elections}
Nombre de communes: {total_communes}
Participation moyenne: {avg_participation:.1f}%

=== NOUVELLES DÉCOUVERTES ===

1. COMPORTEMENT ÉLECTORAL
   - Volatilité politique moyenne: {avg_volatility:.3f}
   - Corrélation participation-revenus: {corr_participation_revenu:.3f}
   - Évolution des votes blancs/nuls analysée

2. FACTEURS SOCIO-ÉCONOMIQUES
   - Impact du revenu médian sur la participation
   - Relation chômage-vote protestataire: {corr_chomage_protestataire:.3f}
   - Influence de la démographie locale

3. PATTERNS TERRITORIAUX
   - Analyse par taille de commune
   - Impact de l'évolution démographique
   - Relation associations-vote écologique

4. TENDANCES TEMPORELLES
   - Évolution spécifique par candidat/parti
   - Diversité politique par type d'élection
   - Changements de leadership communal

=== GRAPHIQUES GÉNÉRÉS ===
- analyse_comportement_electeur.png (4 sous-graphiques)
- impact_socioeconomique.png (6 corrélations)
- volatilite_politique.png (4 analyses)
- performance_candidats.png (4 visualisations)
- patterns_demographiques.png (6 relations)

Total: 5 graphiques avec 23 visualisations détaillées

=== RECOMMANDATIONS POUR ANALYSES FUTURES ===
- Approfondir l'analyse des micro-tendances locales
- Intégrer des données qualitatives sur les enjeux locaux
- Développer des modèles prédictifs par segmentation démographique
- Analyser l'impact des événements politiques nationaux
"""

    report_path = output_dir / 'rapport_analyses_avancees.txt'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✓ Rapport de synthèse sauvegardé: {report_path}")

def main():
    """Fonction principale d'exécution des analyses avancées"""
    setup_matplotlib()
    
    # Création du répertoire de sortie
    output_dir = Path('/app/reports/advanced')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("🔍 Chargement des données...")
    df = load_data()
    
    print("📊 Génération des analyses avancées...")
    
    print("\n1️⃣  Analyse du comportement électoral...")
    analyze_voter_behavior(df, output_dir)
    
    print("\n2️⃣  Impact des facteurs socio-économiques...")
    analyze_socioeconomic_impact(df, output_dir)
    
    print("\n3️⃣  Analyse de la volatilité politique...")
    analyze_political_volatility(df, output_dir)
    
    print("\n4️⃣  Performance des candidats dans le temps...")
    analyze_candidate_performance(df, output_dir)
    
    print("\n5️⃣  Patterns démographiques et géographiques...")
    analyze_demographic_patterns(df, output_dir)
    
    print("\n📋 Génération du rapport de synthèse...")
    generate_summary_report(df, output_dir)
    
    print(f"""
✅ ANALYSES AVANCÉES TERMINÉES !

📁 Répertoire de sortie: {output_dir}
📊 5 graphiques générés avec 23 visualisations
📋 Rapport de synthèse disponible

🔍 Nouvelles insights découvertes:
   • Corrélations socio-économiques détaillées
   • Volatilité politique par commune
   • Patterns démographiques spécifiques
   • Evolution temporelle des candidats
   • Comportements électoraux approfondis
    """)

if __name__ == '__main__':
    main()