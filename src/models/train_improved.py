#!/usr/bin/env python3
"""
Module d'entraînement amélioré pour les modèles de prédiction électorale.

Améliorations apportées:
1. Gestion du déséquilibre des classes avec SMOTE
2. Engineering des features amélioré
3. Validation croisée stratifiée temporelle
4. Optimisation des hyperparamètres avec GridSearchCV
5. Métriques de performance étendues

Auteur: Équipe MSPR Nantes - Version Corrigée
Date: 2024-2025
"""
import argparse, os, sys, json, joblib
import numpy as np
import pandas as pd
from collections import Counter

# Sklearn imports
from sklearn.model_selection import train_test_split, GridSearchCV, StratifiedKFold, TimeSeriesSplit
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.feature_selection import SelectKBest, f_classif
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from sklearn.metrics import (accuracy_score, f1_score, confusion_matrix, 
                           classification_report, precision_recall_fscore_support,
                           balanced_accuracy_score, cohen_kappa_score)

# Imblearn pour gérer le déséquilibre
from imblearn.over_sampling import SMOTE
from imblearn.pipeline import Pipeline as ImblearnPipeline

# Visualization
import matplotlib.pyplot as plt
import seaborn as sns

# Local imports - définition des fonctions inline pour éviter les imports
def ensure_dir(path):
    """Crée un répertoire de façon sécurisée s'il n'existe pas déjà"""
    os.makedirs(path, exist_ok=True)

def read_csv_safe(path, **kwargs):
    """Lecture robuste de fichiers CSV avec détection d'encoding"""
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)

def analyze_class_distribution(y, title="Distribution des classes"):
    """Analyse la distribution des classes et retourne les statistiques"""
    class_counts = Counter(y)
    total = len(y)
    
    print(f"\n=== {title} ===")
    for classe, count in class_counts.most_common():
        pct = (count / total) * 100
        print(f"{classe}: {count} ({pct:.1f}%)")
    
    # Détection du déséquilibre
    max_count = max(class_counts.values())
    min_count = min(class_counts.values())
    imbalance_ratio = max_count / min_count
    
    print(f"Ratio de déséquilibre: {imbalance_ratio:.2f}")
    if imbalance_ratio > 2:
        print("Desequilibre detecte - SMOTE sera applique")
    
    return class_counts, imbalance_ratio

def create_advanced_features(df):
    """Crée des features avancées pour améliorer la prédiction"""
    df_features = df.copy()
    
    print("Creation de features avancees...")
    
    # 1. Features temporelles
    if 'annee' in df_features.columns:
        df_features['annee_normalized'] = (df_features['annee'] - df_features['annee'].min()) / (df_features['annee'].max() - df_features['annee'].min())
        df_features['election_cycle'] = df_features['annee'] % 5  # Cycle electoral francais
    
    # 2. Features d'interaction socio-economique
    if all(col in df_features.columns for col in ['revenu_median_uc_euros', 'taux_chomage_pct']):
        df_features['revenu_chomage_ratio'] = df_features['revenu_median_uc_euros'] / (df_features['taux_chomage_pct'] + 1)
    
    if all(col in df_features.columns for col in ['taux_pauvrete_pct', 'taux_chomage_pct']):
        df_features['precarite_index'] = df_features['taux_pauvrete_pct'] + df_features['taux_chomage_pct']
    
    # 3. Features de participation et engagement politique
    if 'turnout_pct' in df_features.columns:
        df_features['participation_category'] = pd.cut(df_features['turnout_pct'], 
                                                      bins=[0, 50, 70, 85, 100], 
                                                      labels=['faible', 'moderee', 'forte', 'tres_forte'])
    
    # 4. Features de densite et urbanite
    if all(col in df_features.columns for col in ['population', 'entreprises_actives']):
        df_features['densite_economique'] = df_features['entreprises_actives'] / (df_features['population'] + 1) * 1000
    
    if 'population' in df_features.columns:
        df_features['taille_commune'] = pd.cut(df_features['population'], 
                                              bins=[0, 2000, 10000, 50000, np.inf], 
                                              labels=['tres_petite', 'petite', 'moyenne', 'grande'])
    
    # 5. Features de stabilite politique (basee sur le precedent gagnant)
    if 'winner_prev' in df_features.columns:
        df_features['continuite_politique'] = (df_features['winner_prev'].notna()).astype(int)
    
    # 6. Features agregees des resultats passes (moyennes mobiles des pourcentages)
    result_cols = [col for col in df_features.columns if col.endswith('_pct') and 'voix_' in col]
    if result_cols:
        for col in result_cols[:5]:  # Limite aux 5 premiers pour eviter trop de features
            if df_features[col].notna().sum() > 10:
                df_features[f'{col}_rolling_mean'] = df_features.groupby('code_commune_insee')[col].transform(
                    lambda x: x.rolling(window=3, min_periods=1).mean()
                )
    
    print(f"{len(df_features.columns) - len(df.columns)} nouvelles features creees")
    return df_features

def build_improved_datasets(path, label_col="famille_politique", test_years=None, drop_estime=True):
    """
    Version améliorée de build_datasets avec engineering des features
    """
    df = read_csv_safe(path)
    
    # Supprime les données estimées si demandé
    if drop_estime and "estime_y" in df.columns:
        initial_count = len(df)
        df = df[~df["estime_y"].astype(bool)].copy()
        print(f"Donnees estimees supprimees: {initial_count - len(df)} observations")
    
    # Vérifie les colonnes essentielles
    needed = ["annee", label_col, "type_scrutin"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")
    
    # Nettoyage des données
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["annee", label_col])
    df = df[df[label_col].astype(str).str.len() > 0]
    
    # Création de features avancées
    df = create_advanced_features(df)
    
    # Analyse de la distribution des classes
    class_counts, imbalance_ratio = analyze_class_distribution(df[label_col], "Distribution initiale")
    
    # Split temporel
    years_sorted = sorted([int(x) for x in df["annee"].dropna().unique()])
    if not test_years:
        test_years = [years_sorted[-1]]
    else:
        test_years = [int(y) for y in test_years]
    
    df_train = df[~df["annee"].isin(test_years)].copy()
    df_test = df[df["annee"].isin(test_years)].copy()
    
    print(f"Train: {len(df_train)} observations, Test: {len(df_test)} observations")
    
    # Colonnes à exclure (mise à jour avec les nouvelles features)
    exclude = set([
        "code_commune_insee", "nom_commune", "code_epci", "date_scrutin",
        "winner_prev", "estime_x", "estime_y", label_col
    ])
    
    # Identification des colonnes catégorielles
    categorical = []
    for col in ["type_scrutin", "tour", "participation_category", "taille_commune"]:
        if col in df.columns:
            categorical.append(col)
    
    # Colonnes numériques (incluant les nouvelles features)
    numeric = [c for c in df.columns 
              if c not in exclude and c not in categorical and pd.api.types.is_numeric_dtype(df[c])]
    
    print(f"Features: {len(numeric)} numeriques, {len(categorical)} categorielles")
    
    # Préparation des données
    y_train = df_train[label_col].astype(str)
    y_test = df_test[label_col].astype(str)
    X_train = df_train[numeric + categorical]
    X_test = df_test[numeric + categorical]
    
    # Analyse de la distribution dans le train/test
    analyze_class_distribution(y_train, "Distribution Train")
    analyze_class_distribution(y_test, "Distribution Test")
    
    return X_train, X_test, y_train, y_test, numeric, categorical, imbalance_ratio > 2

def create_improved_pipeline(numeric_features, categorical_features, use_smote=True, model_type='rf'):
    """
    Crée un pipeline amélioré avec préprocessing et SMOTE si nécessaire
    """
    # Pipeline de preprocessing numérique
    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),  # Médiane plus robuste
        ('scaler', StandardScaler())
    ])
    
    # Pipeline de preprocessing catégoriel
    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))
    ])
    
    # Preprocesseur
    preprocessor = ColumnTransformer([
        ('num', numeric_pipeline, numeric_features),
        ('cat', categorical_pipeline, categorical_features)
    ])
    
    # Sélection de features
    feature_selector = SelectKBest(f_classif, k=min(50, len(numeric_features + categorical_features)))
    
    # Modèles avec hyperparamètres optimisés
    models = {
        'rf': RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            class_weight='balanced',
            random_state=42
        ),
        'logreg': LogisticRegression(
            max_iter=1000,
            class_weight='balanced',
            random_state=42,
            solver='liblinear'
        ),
        'svm': SVC(
            probability=True,
            class_weight='balanced',
            random_state=42,
            gamma='scale'
        )
    }
    
    model = models[model_type]
    
    # Pipeline avec ou sans SMOTE
    if use_smote:
        pipeline = ImblearnPipeline([
            ('preprocessor', preprocessor),
            ('feature_selector', feature_selector),
            ('smote', SMOTE(random_state=42, k_neighbors=1)),  # Réduit à 1 voisin
            ('classifier', model)
        ])
    else:
        pipeline = Pipeline([
            ('preprocessor', preprocessor),
            ('feature_selector', feature_selector),
            ('classifier', model)
        ])
    
    return pipeline

def evaluate_model_comprehensively(model, X_test, y_test, model_name, output_dir):
    """Évaluation complète du modèle avec métriques étendues"""
    y_pred = model.predict(X_test)
    y_pred_proba = model.predict_proba(X_test) if hasattr(model, 'predict_proba') else None
    
    # Métriques de base
    accuracy = accuracy_score(y_test, y_pred)
    balanced_acc = balanced_accuracy_score(y_test, y_pred)
    f1_macro = f1_score(y_test, y_pred, average='macro')
    f1_weighted = f1_score(y_test, y_pred, average='weighted')
    kappa = cohen_kappa_score(y_test, y_pred)
    
    # Métriques par classe
    precision, recall, f1, support = precision_recall_fscore_support(y_test, y_pred, average=None)
    
    # Compilation des résultats
    results = {
        'model': model_name,
        'accuracy': accuracy,
        'balanced_accuracy': balanced_acc,
        'f1_macro': f1_macro,
        'f1_weighted': f1_weighted,
        'cohen_kappa': kappa,
        'n_test': len(y_test)
    }
    
    print(f"\n=== Résultats {model_name.upper()} ===")
    print(f"Accuracy: {accuracy:.3f}")
    print(f"Balanced Accuracy: {balanced_acc:.3f}")
    print(f"F1-Score (macro): {f1_macro:.3f}")
    print(f"F1-Score (weighted): {f1_weighted:.3f}")
    print(f"Cohen's Kappa: {kappa:.3f}")
    
    # Matrice de confusion améliorée
    cm = confusion_matrix(y_test, y_pred)
    labels = sorted(y_test.unique())
    
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels)
    plt.title(f'Matrice de Confusion - {model_name.upper()}')
    plt.ylabel('Vraies Classes')
    plt.xlabel('Classes Prédites')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "figures", f"cm_improved_{model_name}.png"), dpi=300, bbox_inches='tight')
    plt.close()
    
    # Rapport de classification détaillé
    with open(os.path.join(output_dir, f"classification_report_improved_{model_name}.txt"), "w", encoding='utf-8') as f:
        f.write(f"=== RAPPORT DÉTAILLÉ - {model_name.upper()} ===\n\n")
        f.write(f"Métriques globales:\n")
        f.write(f"- Accuracy: {accuracy:.4f}\n")
        f.write(f"- Balanced Accuracy: {balanced_acc:.4f}\n")
        f.write(f"- F1-Score (macro): {f1_macro:.4f}\n")
        f.write(f"- F1-Score (weighted): {f1_weighted:.4f}\n")
        f.write(f"- Cohen's Kappa: {kappa:.4f}\n\n")
        f.write("Rapport de classification sklearn:\n")
        f.write(classification_report(y_test, y_pred, zero_division=0))
    
    return results, y_pred, y_pred_proba

def hyperparameter_tuning(pipeline, X_train, y_train, model_type='rf'):
    """Optimisation des hyperparamètres avec GridSearchCV"""
    print(f"Optimisation des hyperparametres pour {model_type}...")
    
    param_grids = {
        'rf': {
            'classifier__n_estimators': [100, 200, 300],
            'classifier__max_depth': [10, 15, 20, None],
            'classifier__min_samples_split': [5, 10, 15],
            'feature_selector__k': [20, 30, 40]
        },
        'logreg': {
            'classifier__C': [0.1, 1, 10, 100],
            'classifier__penalty': ['l1', 'l2'],
            'feature_selector__k': [20, 30, 40]
        },
        'svm': {
            'classifier__C': [0.1, 1, 10],
            'classifier__gamma': ['scale', 'auto'],
            'feature_selector__k': [20, 30, 40]
        }
    }
    
    # Validation croisée stratifiée
    cv = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    
    grid_search = GridSearchCV(
        pipeline, 
        param_grids[model_type], 
        cv=cv, 
        scoring='f1_macro',
        n_jobs=-1,
        verbose=1
    )
    
    grid_search.fit(X_train, y_train)
    
    print(f"Meilleurs parametres: {grid_search.best_params_}")
    print(f"Meilleur score CV: {grid_search.best_score_:.3f}")
    
    return grid_search.best_estimator_

def main():
    """Fonction principale améliorée"""
    parser = argparse.ArgumentParser(description="Entraînement amélioré des modèles électoraux")
    parser.add_argument("--data", default="data/processed_csv/master_ml.csv")
    parser.add_argument("--label", default="famille_politique")
    parser.add_argument("--test-years", nargs="*", default=None)
    parser.add_argument("--outdir", default="reports")
    parser.add_argument("--models", nargs="+", choices=['rf', 'logreg', 'svm'], 
                       default=['rf'], help="Modèles à entraîner")
    parser.add_argument("--tune-hyperparams", action="store_true", 
                       help="Active l'optimisation des hyperparamètres")
    args = parser.parse_args()
    
    # Création des répertoires
    ensure_dir(os.path.join(args.outdir, "figures"))
    
    print("ENTRAINEMENT AMELIORE DES MODELES ELECTORAUX")
    print("=" * 60)
    
    # Chargement et préparation des données
    X_train, X_test, y_train, y_test, numeric, categorical, needs_smote = build_improved_datasets(
        args.data, args.label, args.test_years
    )
    
    print(f"SMOTE sera {'applique' if needs_smote else 'ignore'}")
    
    # Entraînement des modèles
    all_results = []
    
    for model_type in args.models:
        print(f"\n{'='*20} MODÈLE {model_type.upper()} {'='*20}")
        
        # Création du pipeline
        pipeline = create_improved_pipeline(numeric, categorical, needs_smote, model_type)
        
        # Optimisation des hyperparamètres si demandé
        if args.tune_hyperparams:
            pipeline = hyperparameter_tuning(pipeline, X_train, y_train, model_type)
        
        # Entraînement
        print(f"Entrainement du modele {model_type}...")
        pipeline.fit(X_train, y_train)
        
        # Évaluation
        results, y_pred, y_pred_proba = evaluate_model_comprehensively(
            pipeline, X_test, y_test, model_type, args.outdir
        )
        all_results.append(results)
        
        # Sauvegarde du modèle
        model_path = os.path.join(args.outdir, f"improved_{model_type}.joblib")
        joblib.dump(pipeline, model_path)
        print(f"Modele sauvegarde: {model_path}")
        
        # Feature importance pour Random Forest
        if model_type == 'rf' and hasattr(pipeline.named_steps['classifier'], 'feature_importances_'):
            try:
                # Récupération des noms de features après preprocessing
                feature_names = pipeline.named_steps['preprocessor'].get_feature_names_out()
                
                # Sélection des features par SelectKBest
                selector = pipeline.named_steps['feature_selector']
                selected_features = feature_names[selector.get_support()]
                
                importances = pipeline.named_steps['classifier'].feature_importances_
                
                # DataFrame des importances
                importance_df = pd.DataFrame({
                    'feature': selected_features,
                    'importance': importances
                }).sort_values('importance', ascending=False)
                
                # Sauvegarde
                importance_df.to_csv(os.path.join(args.outdir, f"feature_importances_improved_{model_type}.csv"), index=False)
                
                print(f"\nTop 10 Features importantes ({model_type}):")
                for _, row in importance_df.head(10).iterrows():
                    print(f"  {row['feature']}: {row['importance']:.4f}")
                    
            except Exception as e:
                print(f"Impossible d'extraire l'importance des features: {e}")
    
    # Sauvegarde des résultats consolidés
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(os.path.join(args.outdir, "improved_metrics.csv"), index=False)
    
    print(f"\nENTRAINEMENT TERMINE!")
    print(f"Resultats sauvegardes dans: {args.outdir}")
    print(f"Metriques: improved_metrics.csv")
    
    # Affichage du classement des modèles
    if len(results_df) > 1:
        print(f"\nCLASSEMENT DES MODELES (F1-macro):")
        ranking = results_df.sort_values('f1_macro', ascending=False)
        for i, (_, row) in enumerate(ranking.iterrows(), 1):
            print(f"  {i}. {row['model'].upper()}: {row['f1_macro']:.3f}")

if __name__ == "__main__":
    main()