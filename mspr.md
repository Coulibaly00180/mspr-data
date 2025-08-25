# MSPR Big Data & Analyse de Données - Dossier de Synthèse

## 1. Contexte & Objectifs

L'objectif de ce projet est de réaliser une preuve de concept (POC) pour la start-up de M. de la Motte Rouge. Cette POC vise à prédire le parti politique qui arrivera en tête lors des élections sur un territoire géographique donné, en se basant sur des données électorales passées et des indicateurs socio-économiques.

Ce dossier retrace la démarche suivie, les choix effectués et les résultats obtenus.

## 2. Choix du Périmètre et des Données

### 2.1. Zone Géographique

**Choix :** La métropole de Nantes (EPCI 244400404), qui comprend 24 communes.

**Justification :**
*   **Périmètre défini :** Il s'agit d'un territoire cohérent et bien délimité.
*   **Disponibilité des données :** Les données électorales et socio-économiques sont facilement accessibles pour ce territoire via les sources gouvernementales (data.gouv.fr, INSEE).
*   **Taille pertinente pour une POC :** Avec 24 communes, le jeu de données est suffisamment grand pour être intéressant, tout en restant gérable pour une preuve de concept.

### 2.2. Critères et Données

**Sources de données utilisées :**
*   **Résultats électoraux :** Fichiers détaillés par commune pour les élections présidentielles, législatives, et européennes de 2012 à 2022 (`*_par_commune.csv`).
*   **Indicateurs socio-économiques :** Données de l'INSEE sur la population, le revenu médian, le taux de chômage, etc. (`indicateurs_2012_2022.csv`).
*   **Référentiels :** Liste des communes de la métropole (`communes_nantes_metropole.csv`) et table des nuances politiques (`nuances_politiques.csv`).

**Justification :**
Ces données ont été choisies car elles sont directement liées à la problématique de la start-up : prédire les tendances de vote en se basant sur le contexte socio-économique, comme mentionné dans le cahier des charges.

## 3. Démarche et Méthodologie

### 3.1. Schéma de Traitement des Données (Flux)

Le flux de données est divisé en deux scripts principaux. Voici une représentation détaillée de chaque étape :

```mermaid
flowchart TD
    subgraph Phase 1: ETL (src/etl/build_master.py)
        direction TB
        A[<b>1. Extraction</b><br>Lecture des CSV bruts<br>(élections, socio-éco, etc.)] --> B[<b>2. Transformation</b><br>- Pivot des données par scrutin<br>- Calcul de la cible 'parti_en_tete'<br>- Fusion avec les indicateurs socio-éco]
        B --> C[<b>3. Chargement</b><br>Sauvegarde du jeu de données unifié]
    end

    C --> D[data/processed_csv/master_ml.csv]

    subgraph Phase 2: Entraînement & Évaluation (src/models/train.py)
        direction TB
        E[<b>4. Préparation</b><br>- Imputation des valeurs manquantes<br>- Encodage de la variable cible<br>- Mise à l'échelle des features] --> F[<b>5. Division des données</b><br>Création des jeux d'entraînement et de test]
        F --> G[<b>6. Entraînement</b><br>Itération sur plusieurs modèles<br>(LogReg, RandomForest...)]
        G --> H[<b>7. Évaluation</b><br>Calcul des métriques<br>sur le jeu de test]
    end

    D --> E
    H --> I[reports/*<br>(Rapports, métriques, figures)]
```

### 3.2. Architecture et Outils

*   **Langage :** Python 3.11
*   **Librairies principales :** Pandas pour la manipulation des données, Scikit-learn pour la modélisation, Matplotlib pour la visualisation.
*   **Environnement :** Le projet est entièrement conteneurisé avec Docker et Docker Compose pour garantir la reproductibilité.
*   **Architecture des données :**
    *   `data/raw_csv/` : Stockage des données brutes.
    *   `data/processed_csv/` : Stockage du jeu de données nettoyé et prêt à l'emploi (`master_ml.csv`).
    *   `reports/` : Stockage des résultats des modèles (métriques, matrices de confusion).

### 3.3. Modèle Conceptuel de Données (MCD)

Voici une représentation des relations entre les différentes données sources utilisées pour ce projet.

```mermaid
erDiagram
    EPCI ||--|{ COMMUNE : "contient"
    COMMUNE ||--o{ RESULTAT : "a pour"
    ELECTION ||--o{ RESULTAT : "concerne"
    CANDIDAT_LISTE ||--o{ RESULTAT : "obtient un"
    NUANCE_POLITIQUE ||--|{ CANDIDAT_LISTE : "est de"
    COMMUNE ||--o{ INDICATEUR_SOCIO_ECO : "a"

    EPCI {
        string code_epci PK "Code de l'EPCI"
        string nom_epci "Nom de l'EPCI"
    }

    COMMUNE {
        string code_commune_insee PK "Code INSEE"
        string nom_commune "Nom"
        string code_epci FK
    }

    ELECTION {
        int annee PK "Année"
        string type_scrutin PK "Type de scrutin"
        int tour PK "Tour"
    }

    CANDIDAT_LISTE {
        string nom_tete_liste PK "Nom Tête de Liste"
        string code_nuance FK "Code Nuance"
    }

    RESULTAT {
        string code_commune_insee FK
        int annee_election FK
        string type_scrutin_election FK
        int tour_election FK
        string nom_candidat FK
        int voix "Nombre de voix"
        float voix_pct "Pourcentage de voix"
    }

    INDICATEUR_SOCIO_ECO {
        string code_commune_insee FK
        int annee "Année"
        float population "Population"
        float revenu_median "Revenu médian"
        float taux_chomage "Taux de chômage"
    }

    NUANCE_POLITIQUE {
        string code_nuance PK "Code Nuance"
        string libelle "Libellé"
        string famille_politique "Famille politique"
    }
```

## 4. Nettoyage et Préparation des Données (ETL)

Le travail le plus conséquent a été réalisé sur le script ETL `src/etl/build_master.py`.

**Actions réalisées :**
1.  **Correction de la source de données :** Le script a été modifié pour utiliser les fichiers `*_par_commune.csv` qui sont plus riches et détaillés, au lieu du fichier `elections_master.csv` qui était incomplet.
2.  **Création de la variable cible :** La colonne `parti_en_tete` (notre variable à prédire) est maintenant calculée automatiquement en identifiant le parti avec le plus de voix pour chaque scrutin.
3.  **Gestion des valeurs manquantes :** Le script d'entraînement a été amélioré pour imputer les valeurs manquantes (NaN) en utilisant la moyenne pour les variables numériques et la valeur la plus fréquente pour les variables catégorielles.
4.  **Création de features :** Le script calcule déjà des features de base comme le taux de participation (`turnout_pct`) et le vainqueur précédent (`winner_prev`).

**Jeu de données final :**
Le résultat de ce processus est le fichier `data/processed_csv/master_ml.csv`, qui est un jeu de données nettoyé, normalisé et optimisé.

## 5. Modélisation

### 5.1. Modèles Testés

Nous avons testé quatre modèles de classification standards, comme implémenté dans `src/models/train.py` :
*   **Régression Logistique :** Un modèle linéaire simple et interprétable.
*   **Random Forest :** Un modèle d'ensemble (basé sur les arbres de décision) plus complexe et souvent plus performant.

### 5.2. Résultats et Précision (Accuracy)

Après avoir standardisé les étiquettes des partis politiques en grandes familles, les modèles ont été ré-entraînés. Les performances se sont très nettement améliorées :

| model           |   accuracy |   f1_macro |   n_train |   n_test | test_years   |
|:----------------|-----------:|-----------:|----------:|---------:|:-------------|
| logreg          |   0.666667 |   0.4      |       240 |       72 | 2022         |
| random_forest   |   0.666667 |   0.4      |       240 |       72 | 2022         |
| svm             |   0.666667 |   0.333333 |       240 |       72 | 2022         |
| xgboost         |   0.291667 |   0.152174 |       240 |       72 | 2022         |

**Analyse :**
*   La **Régression Logistique** et le **Random Forest** obtiennent les meilleurs scores, avec une précision de **66.7%** et un F1-score de 0.4. Cela signifie qu'ils prédisent correctement le parti en tête dans deux tiers des cas sur les données de test, ce qui est un résultat très encourageant pour une POC.
*   Le modèle **SVM** atteint la même précision mais avec un F1-score plus faible, ce qui indique qu'il est moins performant sur l'équilibre précision/rappel.
*   Le modèle **XGBoost** a des performances très faibles, ce qui est inattendu. Cela pourrait être dû à un problème de configuration des hyperparamètres ou à la petite taille du jeu de données.

Compte tenu de ces résultats, la Régression Logistique et le Random Forest sont deux candidats viables. Nous utiliserons le modèle Random Forest pour analyser l'importance des caractéristiques en raison de sa nature arborescente, qui rend cette analyse simple.

Les matrices de confusion et les rapports de classification détaillés pour chaque modèle sont disponibles dans le dossier `reports/`.

### 5.3. Choix du Modèle Final

Compte tenu des résultats, les modèles `LogisticRegression` et `RandomForestClassifier` sont les plus performants.

Pour l'analyse des données et la compréhension des facteurs d'influence, le **Random Forest** est un excellent outil. Comme nous l'avons vu dans la section 7.1, sa nature lui permet de calculer facilement l'importance de chaque variable, nous aidant à comprendre *quelles* données sont les plus prédictives.

Cependant, pour le modèle final à présenter pour cette preuve de concept, nous recommandons la **Régression Logistique**.

**Justification :**
*   **Principe de parcimonie (ou Rasoir d'Ockham) :** Entre deux modèles aux performances égales, il est préférable de choisir le plus simple. La Régression Logistique est un modèle linéaire beaucoup plus simple et moins coûteux en ressources qu'une Forêt Aléatoire.
*   **Interprétabilité :** C'est l'atout majeur ici. Il est beaucoup plus facile d'interpréter les coefficients d'une Régression Logistique pour comprendre *comment* chaque variable influence la prédiction (positivement ou négativement). Cela répond directement à la problématique de l'entreprise : "mieux comprendre ses clients" et fournir des analyses claires.

## 6. Visualisations

Pour illustrer les résultats, voici une série de cartes représentant le parti arrivé en tête dans chaque commune de la métropole de Nantes pour les différentes élections.

### Présidentielles

| 2012 - Tour 1 | 2012 - Tour 2 |
| :---: | :---: |
| ![Carte des résultats de la présidentielle 2012, T1](reports/figures/map_2012_pres_t1.png) | ![Carte des résultats de la présidentielle 2012, T2](reports/figures/map_2012_pres_t2.png) |
| **2017 - Tour 1** | **2017 - Tour 2** |
| ![Carte des résultats de la présidentielle 2017, T1](reports/figures/map_2017_pres_t1.png) | ![Carte des résultats de la présidentielle 2017, T2](reports/figures/map_2017_pres_t2.png) |
| **2022 - Tour 1** | **2022 - Tour 2** |
| ![Carte des résultats de la présidentielle 2022, T1](reports/figures/map_2022_pres_t1.png) | ![Carte des résultats de la présidentielle 2022, T2](reports/figures/map_2022_pres_t2.png) |

### Législatives (Tour 1)

| 2012 | 2017 | 2022 |
| :---: | :---: | :---: |
| ![Carte des résultats des législatives 2012, T1](reports/figures/map_2012_legi_t1.png) | ![Carte des résultats des législatives 2017, T1](reports/figures/map_2017_legi_t1.png) | ![Carte des résultats des législatives 2022, T1](reports/figures/map_2022_legi_t1.png) |

### Européennes (Tour 1)

| 2014 | 2019 |
| :---: | :---: |
| ![Carte des résultats des européennes 2014, T1](reports/figures/map_2014_euro_t1.png) | ![Carte des résultats des européennes 2019, T1](reports/figures/map_2019_euro_t1.png) |

### Municipales (Tour 1)

| 2014 | 2020 |
| :---: | :---: |
| ![Carte des résultats des municipales 2014, T1](reports/figures/map_2014_muni_t1.png) | ![Carte des résultats des municipales 2020, T1](reports/figures/map_2020_muni_t1.png) |


## 7. Réponses aux Indicateurs d'Analyse

### 7.1. Corrélation entre données et résultats

Le modèle Random Forest nous permet d'estimer l'importance de chaque feature (variable) dans la prédiction. C'est une étape cruciale pour répondre à la question métier : "Quelles sont les données les plus corrélées avec les résultats des élections ?".

Après avoir entraîné le modèle, nous avons extrait l'importance de chaque variable. Voici le top 10 des features les plus influentes :

| Feature                      |   Importance |
|:-----------------------------|-------------:|
| `num__voix_pct_other`        |      0.064232 |
| `num__voix_pct_modem`        |      0.0576   |
| `num__annee`                 |      0.057165 |
| `num__other_pct`             |      0.055446 |
| `num__modem_pct`             |      0.049836 |
| `num__eelv_pct`              |      0.044559 |
| `num__turnout_pct`           |      0.041283 |
| `num__revenu_median_uc_euros`|      0.040085 |
| `num__taux_chomage_pct`      |      0.039654 |
| `num__voix_pct_eelv`         |      0.037899 |

**Analyse :**
*   **L'historique électoral est clé :** Les variables les plus importantes sont liées aux résultats des scrutins précédents (ex: `voix_pct_other`, `voix_pct_modem`). Cela confirme que le comportement de vote passé est un excellent prédicteur du comportement futur. L'année de l'élection (`annee`) est également très importante, ce qui est logique puisque les tendances politiques évoluent dans le temps.
*   **Les facteurs socio-économiques comptent :** Des indicateurs comme le revenu médian (`revenu_median_uc_euros`) et le taux de chômage (`taux_chomage_pct`) apparaissent dans le top 10, ce qui valide l'hypothèse de départ du projet.
*   **La participation est un facteur :** Le taux de participation (`turnout_pct`) joue également un rôle non négligeable.

Cette analyse fournit une réponse claire à la question initiale et permet à l'entreprise de concentrer ses efforts sur la collecte de ces données spécifiques pour ses futurs modèles.

La liste complète de l'importance des variables est disponible dans le fichier `reports/feature_importances_rf.csv`.

### 7.2. Principe de l'apprentissage supervisé
L'apprentissage supervisé est une branche du machine learning où l'on entraîne un modèle sur un jeu de données "étiqueté". Dans notre cas, les "données" sont les indicateurs socio-économiques et les résultats des élections passées, et l'"étiquette" (la "bonne réponse" que le modèle doit apprendre à prédire) est la colonne `parti_en_tete`. Le modèle apprend à trouver les relations entre les données et l'étiquette pour pouvoir ensuite prédire l'étiquette sur de nouvelles données qu'il n'a jamais vues.

### 7.3. Définition de la précision (Accuracy)
L'accuracy (ou précision globale) est une métrique qui mesure la performance d'un modèle de classification. Elle est calculée simplement par la formule :
**Accuracy = (Nombre de prédictions correctes) / (Nombre total de prédictions)**
Par exemple, si notre modèle prédit correctement le parti en tête pour 80 des 100 élections du jeu de test, son accuracy est de 80%. Bien que simple à comprendre, cette métrique peut être trompeuse si les classes sont déséquilibrées. C'est pourquoi nous regardons aussi le F1-score, qui est une moyenne harmonique de la précision et du rappel.

## 8. Code Source

Le code source complet, propre et commenté, se trouve dans le répertoire `src/` de ce projet.

---

## Ce qu'il nous manque (TODO)

Voici la liste des tâches restantes pour finaliser le projet selon le cahier des charges :

-   [x] **Créer le Modèle Conceptuel de Données (MCD)** dans la section 3.3.
-   [x] **Analyser et synthétiser les résultats des modèles** dans la section 5.2.
-   [x] **Générer et insérer les visualisations** (cartes, graphiques) dans la section 6.
-   [x] **Déterminer les données les plus corrélées** aux résultats en analysant l'importance des features du modèle (section 7.1).
-   [x] **(Optionnel) Améliorer les modèles** en testant d'autres algorithmes ou en optimisant les hyperparamètres.
-   [x] **(Optionnel) Ajouter des commentaires** plus détaillés dans le code source si nécessaire.
-   [x] **(Optionnel) Nettoyer les fichiers `docker-compose.yml`** en enlevant l'attribut `version`.
