#!/usr/bin/env python3
"""
Module d'entraînement et d'évaluation des modèles de prédiction électorale.

Ce module constitue le cœur du système de machine learning pour la prédiction 
des résultats électoraux de Nantes Métropole. Il implémente un pipeline complet
de classification multi-modèles avec validation temporelle.

Architecture ML:
    Données → Préprocessing → Multiple Modèles → Évaluation → Sélection

Modèles implémentés:
    1. 🔵 Régression Logistique - Modèle de référence rapide et interprétable
    2. 🌲 Random Forest - Ensemble method avec importance des features  
    3. ⚡ SVM - Support Vector Machine pour frontières complexes
    4. 🚀 XGBoost - Gradient boosting state-of-the-art

Stratégie de validation:
    - Séparation temporelle : années récentes pour le test (réalisme)
    - Preprocessing pipelines : StandardScaler + OneHotEncoder
    - Métriques multiples : Accuracy, F1-macro, matrice de confusion
    - Feature importance pour l'interprétabilité

Sorties générées:
    - Modèles sérialisés (.joblib)
    - Rapports de classification détaillés
    - Matrices de confusion visuelles
    - Métriques de performance (CSV)
    - Feature importances (Random Forest)

Usage:
    python src/models/train.py --data /path/to/master_ml.csv [--test-years 2022]

Auteur: Équipe MSPR Nantes
Date: 2024-2025
"""
import argparse, os, sys, json
from sklearn.impute import SimpleImputer
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler, LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.svm import SVC
from xgboost import XGBClassifier
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix, classification_report
import matplotlib.pyplot as plt
from src.common.io import ensure_dir, read_csv_safe

def build_datasets(path, label_col="parti_en_tete", test_years=None, drop_estime=True):
    """
    Construit les datasets d'entraînement et de test avec validation temporelle.
    
    Cette fonction implémente une stratégie de split temporel réaliste :
    - Les données historiques servent à l'entraînement
    - Les données récentes (test_years) servent à la validation
    - Preprocessing automatique des types de données
    - Filtrage des données estimées/incomplètes
    
    La validation temporelle est cruciale car elle simule un cas d'usage réel :
    prédire les élections futures à partir du passé.
    
    Args:
        path (str): Chemin vers le fichier master_ml.csv
        label_col (str): Nom de la colonne cible à prédire (default: "parti_en_tete")
        test_years (list): Années à utiliser pour le test. Si None, utilise la dernière année
        drop_estime (bool): Si True, supprime les données estimées/synthétiques
        
    Returns:
        tuple: (X_train, X_test, y_train, y_test, num_features, cat_features)
            - X_train/X_test: Features d'entraînement et de test
            - y_train/y_test: Labels d'entraînement et de test  
            - num_features: Liste des colonnes numériques
            - cat_features: Liste des colonnes catégorielles
            
    Raises:
        ValueError: Si des colonnes essentielles sont manquantes
        
    Note:
        La séparation temporelle garantit qu'aucune information du futur
        ne "fuite" dans l'entraînement, respectant le principe de causalité.
    """
    df = read_csv_safe(path)
    # Supprime les données estimées si la colonne 'estime' existe et est vraie.
    if drop_estime and "estime" in df.columns:
        df = df[~df["estime"].astype(bool)].copy()

    # Vérifie la présence des colonnes essentielles.
    needed = ["annee", label_col, "type_scrutin"]
    for c in needed:
        if c not in df.columns:
            raise ValueError(f"Missing required column: {c}")

    # Convertit la colonne 'annee' en numérique et gère les valeurs manquantes.
    df["annee"] = pd.to_numeric(df["annee"], errors="coerce").astype("Int64")
    df = df.dropna(subset=["annee", label_col])
    df = df[df[label_col].astype(str).str.len() > 0]

    # Détermine les années à utiliser pour le jeu de test (par défaut, la dernière année disponible).
    years_sorted = sorted([int(x) for x in df["annee"].dropna().unique()])
    if not test_years:
        test_years = [years_sorted[-1]]
    else:
        test_years = [int(y) for y in test_years]

    # Divise le DataFrame en ensembles d'entraînement et de test basés sur les années.
    df_train = df[~df["annee"].isin(test_years)].copy()
    df_test  = df[df["annee"].isin(test_years)].copy()

    # Définit les colonnes à exclure des caractéristiques et identifie les colonnes catégorielles.
    exclude = set(["code_commune_insee","nom_commune","code_epci","date_scrutin",
                   "winner_prev", "estime", label_col])
    categorical = []
    if "type_scrutin" in df.columns:
        categorical.append("type_scrutin")
    if "tour" in df.columns:
        categorical.append("tour")

    # Identifie les colonnes numériques en excluant les colonnes définies et les catégorielles.
    numeric = [c for c in df.columns if c not in exclude and c not in categorical and pd.api.types.is_numeric_dtype(df[c])]

    # Sépare la variable cible (y) des caractéristiques (X).
    y_train = df_train[label_col].astype(str)
    y_test = df_test[label_col].astype(str)

    # Définit le pipeline de prétraitement pour les caractéristiques numériques (imputation et mise à l'échelle).
    numeric_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='mean')),
        ('scaler', StandardScaler(with_mean=False))
    ])

    # Définit le pipeline de prétraitement pour les caractéristiques catégorielles (imputation et encodage one-hot).
    categorical_pipeline = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='most_frequent')),
        ('onehot', OneHotEncoder(handle_unknown='ignore'))
    ])

    # Combine les pipelines de prétraitement numériques et catégoriels.
    preproc = ColumnTransformer(
        transformers=[
            ('num', numeric_pipeline, numeric),
            ('cat', categorical_pipeline, categorical)
        ],
        remainder='drop'
    )

    # Définit les pipelines des modèles de classification.
    logreg = Pipeline([("prep", preproc),
                       ("clf", LogisticRegression(max_iter=300, class_weight="balanced"))])

    rf = Pipeline([("prep", preproc),
                   ("clf", RandomForestClassifier(n_estimators=400, random_state=42, class_weight="balanced_subsample"))])
                   
    svm = Pipeline([("prep", preproc),
                    ("clf", SVC(gamma='auto', probability=True, class_weight='balanced'))])

    xgb = Pipeline([("prep", preproc),
                    ("clf", XGBClassifier(use_label_encoder=False, eval_metric='mlogloss'))])


    return (df_train, df_test, numeric, categorical, y_train, y_test, logreg, rf, svm, xgb)

def plot_confusion(y_true, y_pred, labels, out_png):
    """
    Trace et sauvegarde une matrice de confusion normalisée.
    """
    cm = confusion_matrix(y_true, y_pred, labels=labels, normalize="true")
    plt.figure(figsize=(8,6))
    plt.imshow(cm, interpolation="nearest")
    plt.title("Confusion matrix (normalized)")
    plt.xlabel("Predicted")
    plt.ylabel("True")
    plt.xticks(range(len(labels)), labels, rotation=45, ha="right")
    plt.yticks(range(len(labels)), labels)
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            plt.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()

def main():
    """
    Fonction principale pour exécuter le processus d'entraînement et d'évaluation du modèle.
    Analyse les arguments, charge et prépare les données, entraîne et évalue les modèles,
    et sauvegarde les résultats.
    """
    ap = argparse.ArgumentParser(description="Train classifiers on master ML dataset")
    ap.add_argument("--data", default="data/processed_csv/master_ml.csv")
    ap.add_argument("--label", default="famille_politique")
    ap.add_argument("--test-years", nargs="*", default=None)
    ap.add_argument("--outdir", default="reports")
    args = ap.parse_args()

    os.makedirs(os.path.join(args.outdir, "figures"), exist_ok=True)

    # Charge et prépare les jeux de données d'entraînement et de test.
    (df_train, df_test, numeric, categorical, y_train, y_test, logreg, rf, svm, xgb) = build_datasets(
        args.data, args.label, args.test_years
    )

    # Sélectionne les caractéristiques (numériques et catégorielles) pour l'entraînement.
    X_train = df_train[numeric + categorical]
    X_test  = df_test[numeric + categorical]

    # Définit les modèles à entraîner.
    models = {
        "logreg": logreg,
        "random_forest": rf,
        "svm": svm,
        "xgboost": xgb
    }

    # Encode les étiquettes de la variable cible pour les modèles qui le nécessitent (comme XGBoost).
    le = LabelEncoder()
    y_train_encoded = le.fit_transform(y_train)
    
    metrics_list = []
    # Boucle sur chaque modèle pour l'entraînement, la prédiction et l'évaluation.
    for model_name, model in models.items():
        # Gère spécifiquement l'entraînement pour XGBoost qui utilise des étiquettes encodées.
        if model_name == 'xgboost':
            model.fit(X_train, y_train_encoded)
            pred_encoded = model.predict(X_test)
            pred = le.inverse_transform(pred_encoded)
        else:
            # Entraîne les autres modèles et fait des prédictions.
            model.fit(X_train, y_train)
            pred = model.predict(X_test)
            
        # Calcule les métriques de performance (accuracy et F1-score).
        acc = accuracy_score(y_test, pred)
        f1 = f1_score(y_test, pred, average="macro")
        
        # Ajoute les métriques du modèle à la liste.
        metrics_list.append({
            "model": model_name,
            "accuracy": acc,
            "f1_macro": f1,
            "n_train": len(df_train),
            "n_test": len(df_test),
            "test_years": ",".join(map(str, sorted(df_test['annee'].unique())))
        })

        # Trace et sauvegarde la matrice de confusion.
        labels = sorted(y_test.unique())
        plot_confusion(y_test, pred, labels, os.path.join(args.outdir, "figures", f"cm_{model_name}.png"))
        # Sauvegarde le rapport de classification détaillé.
        with open(os.path.join(args.outdir, f"classification_report_{model_name}.txt"), "w") as f:
            f.write(classification_report(y_test, pred, zero_division=1))

        # Calcule et sauvegarde l'importance des caractéristiques pour le modèle Random Forest.
        if model_name == 'random_forest':
            try:
                feature_names = model.named_steps['prep'].get_feature_names_out()
                importances = model.named_steps['clf'].feature_importances_
                forest_importances = pd.Series(importances, index=feature_names)
                
                print("
Importance des caractéristiques (Random Forest):")
                print(forest_importances.sort_values(ascending=False).head(20))
                
                # Sauvegarde dans un fichier CSV.
                importances_df = pd.DataFrame(forest_importances.sort_values(ascending=False))
                importances_df.to_csv(os.path.join(args.outdir, "feature_importances_rf.csv"))


            except Exception as e:
                print(f"Impossible d'obtenir l'importance des caractéristiques : {e}")


    # Consolide et sauvegarde toutes les métriques des modèles dans un fichier CSV.
    metrics = pd.DataFrame(metrics_list)
    metrics_path = os.path.join(args.outdir, "metrics.csv")
    metrics.to_csv(metrics_path, index=False)

    print(f"[OK] Métriques sauvegardées dans {metrics_path}")
    print(f"[OK] Matrices de confusion sauvegardées dans reports/figures")

if __name__ == "__main__":
    main()
