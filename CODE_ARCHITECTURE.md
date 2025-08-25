# 🏗️ ARCHITECTURE DU CODE - Projet MSPR Nantes

## Vue d'ensemble du projet

Ce projet implémente un pipeline complet d'analyse et de prédiction électorale pour Nantes Métropole, combinant ETL, Machine Learning et visualisations avancées dans une architecture containerisée.

---

## 📁 Structure des répertoires

```
mspr-nantes-docker-v3/
├── 📂 src/                          # Code source principal
│   ├── 📂 common/                   # Modules utilitaires partagés
│   ├── 📂 etl/                      # Extract, Transform, Load  
│   ├── 📂 models/                   # Machine Learning
│   └── 📂 viz/                      # Visualisations et analyses
├── 📂 data/                         # Données (non versionnées)
│   ├── 📂 raw_csv/                  # Données sources brutes
│   └── 📂 processed_csv/            # Données transformées
├── 📂 reports/                      # Sorties générées
│   ├── 📂 trends/                   # Analyses temporelles
│   ├── 📂 geographic/               # Cartographie
│   ├── 📂 interactive/              # Dashboards web
│   └── 📂 advanced/                 # Analyses approfondies
├── 📂 docs/                         # Documentation
├── 🐳 Dockerfile                    # Container de production
├── 🐳 docker-compose.yml            # Orchestration Docker
├── 📋 requirements.txt              # Dépendances Python
├── 🛠️ Makefile                     # Commandes automatisées
└── 📖 README.md                     # Guide utilisateur
```

---

## 🔄 Pipeline d'exécution

### 1. Point d'entrée principal
```python
src/run_pipeline.py
```
**Rôle :** Orchestrateur du pipeline ML complet
- ✅ Exécute l'ETL (build_master.py)
- ✅ Lance l'entraînement des modèles (train.py)  
- ✅ Gestion d'erreurs robuste
- ✅ Support des variables d'environnement

### 2. ETL (Extract, Transform, Load)
```python
src/etl/build_master.py
```
**Rôle :** Construction du dataset unifié
- 📥 Chargement des données brutes CSV
- 🔧 Harmonisation des schémas
- 🔗 Jointures avec données socio-économiques  
- ⚙️ Feature engineering avancé
- 💾 Export vers master_ml.csv

**Modules associés :**
```python
src/etl/fetch_geojson.py    # Récupération géométries communes
src/etl/export_map.py       # Export cartographique
```

### 3. Machine Learning
```python
src/models/train.py
```
**Rôle :** Entraînement et évaluation des modèles
- 🤖 4 algorithmes : LogisticRegression, RandomForest, SVM, XGBoost
- ⏰ Validation temporelle réaliste
- 📊 Métriques complètes (accuracy, F1, confusion matrix)
- 💾 Sérialisation des modèles (.joblib)
- 📈 Feature importance (Random Forest)

---

## 📊 Système de visualisation

### 4. Orchestrateur de visualisations
```python
src/viz/run_all_visualizations.py
```
**Rôle :** Point d'entrée unique pour toutes les analyses
- 🎯 Exécute les 4 modules d'analyse
- 📋 Génère un rapport de synthèse JSON
- 🌐 Crée l'index HTML global
- ⚡ Gestion d'erreurs tolérante

### 5. Module d'audit qualité
```python
src/audit_winner.py
```
**Rôle :** Contrôle qualité des données
- 🔍 Détecte les élections "monochromes" (92%)
- 📊 Analyse de la diversité politique
- ⚠️ Alertes sur la fiabilité prédictive
- 📄 Export CSV des métriques d'audit

### 6. Analyses temporelles
```python
src/viz/trends_analyzer.py
```
**Rôle :** Visualisation des évolutions 2012-2022
- 📈 **5 graphiques générés :**
  - `evolution_familles_politiques.png` - Cycles politiques
  - `evolution_participation.png` - Dynamiques d'abstention
  - `comparaison_scrutins.png` - Logiques par type d'élection
  - `tendances_socioeconomiques.png` - Corrélations sociales  
  - `matrice_correlation.png` - Patterns cachés

### 7. Cartographie électorale
```python
src/viz/geographic_analyzer.py
```
**Rôle :** Analyse spatiale et cartes choroplèthes
- 🗺️ **26 cartes générées :**
  - 13 cartes de résultats par élection
  - 13 cartes de participation associées
- 📊 Analyse de stabilité territoriale
- 🎯 Détection de patterns géographiques
- 📄 Export CSV des métriques communales

### 8. Dashboards interactifs
```python
src/viz/interactive_dashboard.py
```
**Rôle :** Exploration web interactive (Plotly)
- 🌐 **5 dashboards HTML autonomes :**
  - `dashboard_electoral.html` - Vue d'ensemble
  - `timeline_interactive.html` - Chronologie dynamique
  - `participation_heatmap.html` - Carte thermique
  - `party_distribution_sunburst.html` - Hiérarchie partisane
  - `socioeconomic_scatter.html` - Corrélations multivariées

### 9. Analyses avancées
```python
src/viz/advanced_analysis.py
```
**Rôle :** Analyses statistiques approfondies
- 🧮 **23 visualisations en 5 graphiques :**
  - `analyse_comportement_electeur.png` - Patterns de vote
  - `impact_socioeconomique.png` - 6 corrélations sociales
  - `volatilite_politique.png` - Stabilité territoriale
  - `performance_candidats.png` - Évolution des leaders
  - `patterns_demographiques.png` - Relations territoire/vote

### 10. Prédictions prospectives
```python
src/viz/future_predictions.py
```
**Rôle :** Projections électorales 2025-2027
- 🔮 Scénarios multiples (continuité, rupture, médian)
- 📊 Intervalles de confiance adaptatifs
- 🗺️ Cartographie prédictive par commune
- ⚠️ Métriques de fiabilité et limitations

---

## 🛠️ Modules utilitaires

### 11. Fonctions I/O robustes
```python
src/common/io.py
```
**Rôle :** Opérations fichiers sécurisées
- 📁 `ensure_dir()` - Création répertoires
- 📖 `read_csv_safe()` - Lecture multi-encodages
- 💾 `write_csv_safe()` - Écriture UTF-8 
- 🔍 `cols_like()` - Sélection par patterns

---

## 🎯 Patterns architecturaux utilisés

### 1. **Pipeline Pattern**
- Chaque étape produit des sorties consommées par la suivante
- Séparation claire des responsabilités
- Possibilité d'exécution partielle/debugging

### 2. **Strategy Pattern**
- Multiple algorithmes ML avec interface commune
- Choix du meilleur modèle basé sur les métriques
- Extensibilité pour nouveaux algorithmes

### 3. **Factory Pattern**
- Génération automatique de visualisations
- Configuration centralisée (matplotlib, plotly)
- Réutilisation des patterns graphiques

### 4. **Observer Pattern**  
- Logging unifié dans tous les modules
- Rapports de progression en temps réel
- Gestion centralisée des erreurs

---

## 🔧 Configuration et déploiement

### Variables d'environnement
```bash
TEST_YEARS=2022         # Années de test ML
OUTPUT_DIR=/app/reports # Répertoire de sortie
```

### Commandes Docker principales
```bash
# Construction
docker compose build

# Pipeline ML complet
docker compose run --rm app python src/run_pipeline.py

# Visualisations complètes  
docker compose run --rm app src/viz/run_all_visualizations.py

# Module spécifique
docker compose run --rm app python src/viz/trends_analyzer.py
```

### Commandes Make automatisées
```bash
make build      # Construction container
make train      # Pipeline ML
make viz        # Toutes visualisations
make audit      # Contrôle qualité
make clean      # Nettoyage
```

---

## 📋 Points d'attention pour les développeurs

### 1. **Gestion des encodages**
- Utiliser `read_csv_safe()` pour les fichiers externes
- Forcer UTF-8 en sortie avec `write_csv_safe()`
- Tester avec des caractères accentués français

### 2. **Validation temporelle ML**
- Ne jamais mélanger années test/train
- Respecter la chronologie dans les splits
- Documenter les hypothèses temporelles

### 3. **Gestion d'erreurs**
- Utiliser des try/except spécifiques
- Logger les erreurs avec contexte
- Permettre l'exécution partielle si possible

### 4. **Performance**
- Optimiser les boucles pandas (vectorisation)
- Limiter les imports lourds (plotly conditionnel)
- Utiliser des backends non-interactifs ('Agg')

### 5. **Reproductibilité**
- Documenter toutes les dépendances
- Fixer les seeds aléatoires si nécessaire
- Tester en environnement Docker propre

---

## 🚀 Extension du projet

### Ajout d'un nouveau modèle ML
1. Modifier `src/models/train.py`
2. Ajouter la configuration dans le dictionnaire `models`
3. Implémenter l'évaluation spécifique si nécessaire
4. Mettre à jour la documentation

### Ajout d'une nouvelle visualisation
1. Créer le module dans `src/viz/`
2. Implémenter les fonctions de base (load_data, setup, export)
3. Ajouter l'appel dans `run_all_visualizations.py`
4. Mettre à jour l'index HTML

### Ajout de nouvelles données
1. Placer les fichiers CSV dans `data/raw_csv/`
2. Adapter `build_master.py` pour l'intégration
3. Mettre à jour les schémas si nécessaire
4. Tester la compatibilité avec les modèles existants

---

## 📞 Support et maintenance

**Points de contact :**
- Documentation technique : `CLAUDE.md`
- Documentation utilisateur : `README.md`
- Analyse complète : `analyse_complete_schemas.md`
- Synthèse académique : `MSPR3_Synthese.md`

**Commandes de debugging :**
```bash
# Vérification environnement
docker compose run --rm app python --version
docker compose run --rm app pip list

# Tests de connectivité données
docker compose run --rm app ls -la /app/data/

# Logs détaillés
docker compose run --rm app python src/audit_winner.py
```

---

Cette architecture modulaire et documentée facilite la maintenance, l'extension et la collaboration sur le projet d'analyse électorale de Nantes Métropole.

**Auteur :** Équipe MSPR Nantes  
**Date :** 25 août 2025  
**Version :** 3.0.0