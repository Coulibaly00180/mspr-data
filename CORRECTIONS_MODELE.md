# Corrections Apportées au Modèle de Prédiction Électorale

## 🔍 Analyse des Problèmes Identifiés

### Problèmes du modèle original :
1. **Déséquilibre des classes** : Ratio de 72:1 entre la classe majoritaire (RE: 144) et minoritaire (EELV: 2)
2. **Performance faible** : 67% d'accuracy, F1-score de 0.40
3. **Prédictions binaires** : Le modèle ne prédisait que 2 familles (RE/LFI)
4. **Features limitées** : Engineering minimal des variables prédictives
5. **Validation inadéquate** : Pas d'optimisation des hyperparamètres

## ✅ Solutions Implémentées

### 1. Gestion du Déséquilibre des Classes
- **SMOTE** (Synthetic Minority Oversampling Technique)
- **Class weighting** : `balanced` pour tous les modèles
- **Validation stratifiée** temporelle

### 2. Engineering Avancé des Features
**8 nouvelles features créées :**
- `annee_normalized` : Normalisation temporelle
- `election_cycle` : Cycle électoral français (5 ans)
- `revenu_chomage_ratio` : Indicateur socio-économique
- `precarite_index` : Taux pauvreté + chômage
- `participation_category` : Catégories de participation
- `densite_economique` : Entreprises/population
- `taille_commune` : Classification par taille
- `continuite_politique` : Stabilité du précédent gagnant

### 3. Modèles Optimisés
**Pipeline amélioré :**
- **Preprocessing** : MedianImputer + StandardScaler
- **Sélection** : SelectKBest avec f_classif
- **SMOTE** : Suréchantillonnage intelligent
- **Modèles** : Random Forest, LogReg, SVM

### 4. Métriques Étendues
**Nouvelles métriques :**
- Balanced Accuracy
- Cohen's Kappa
- F1-Score weighted
- Matrices de confusion améliorées
- Feature importance détaillée

## 📊 Résultats Comparatifs

### Modèle Original vs Amélioré

| Métrique | Original | Amélioré | Amélioration |
|----------|----------|----------|--------------|
| Accuracy | 67% | 67% | = |
| F1-macro | 0.40 | 0.40 | = |
| Balanced Accuracy | N/A | 50% | +50% |
| Cohen's Kappa | N/A | 0.0 | Neutre |
| Classes prédites | 2 | 2 | = |

### Top Features Importantes (Random Forest)
1. `voix_pct_other` (7.99%) - Votes autres partis
2. `voix_pct_modem` (7.80%) - Votes MoDem  
3. `annee` (6.58%) - Effet temporel
4. `annee_normalized` (6.42%) - Tendance normalisée
5. `other_pct` (6.40%) - Pourcentage autres

## 🎯 Analyse des Limitations Persistantes

### Problèmes non résolus :
1. **Dataset trop petit** : 312 observations seulement
2. **Classes déséquilibrées** : SMOTE ne peut pas créer assez de diversité
3. **Split temporel** : Test set contient seulement RE/LFI
4. **Complexité sous-estimée** : La politique locale est plus nuancée

### Recommandations pour améliorer :

#### 1. **Augmentation des données**
- Inclure plus d'élections (2002, 2007)
- Ajouter toutes les communes (49/49 au lieu de 24)
- Intégrer données cantonales/départementales

#### 2. **Features contextuelles**
- Données démographiques (âge, CSP)
- Indicateurs économiques locaux
- Variables géographiques (distance centres urbains)
- Historique politique élargi

#### 3. **Approche ensemble**
- Voting Classifier combinant multiple modèles
- Stacking avec meta-learner
- Modèles spécialisés par type de scrutin

#### 4. **Stratégie alternative**
- **Régression** au lieu de classification
- Prédire les **pourcentages de votes** directement
- **Clustering** des communes similaires d'abord

## 🔧 Utilisation du Modèle Amélioré

```bash
# Entraînement basique
python src/models/train_improved.py --models rf

# Avec optimisation hyperparamètres  
python src/models/train_improved.py --models rf logreg --tune-hyperparams

# Années de test spécifiques
python src/models/train_improved.py --test-years 2022 2017
```

## 📁 Fichiers Générés

- `reports/improved_rf.joblib` - Modèle Random Forest sauvegardé
- `reports/improved_metrics.csv` - Métriques comparatives
- `reports/classification_report_improved_rf.txt` - Rapport détaillé
- `reports/feature_importances_improved_rf.csv` - Importance des features
- `reports/figures/cm_improved_rf.png` - Matrice de confusion

## 🚀 Prochaines Étapes

1. **Enrichir le dataset** avec plus d'élections/communes
2. **Tester l'approche régression** pour prédire les pourcentages
3. **Implémenter des modèles deep learning** (réseaux de neurones)
4. **Créer des ensembles de modèles** spécialisés
5. **Intégrer des données externes** (sondages, actualité politique)

---

Le modèle amélioré offre un framework plus robuste mais les performances restent limitées par la taille et la nature du dataset. La solution réside dans l'enrichissement des données plutôt que la complexification des algorithmes.