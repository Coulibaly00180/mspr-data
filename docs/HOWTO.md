# HOWTO

## 1) Préparer les données

Dépose dans `data/raw_csv/` au minimum :
- `communes_nantes_metropole.csv`
- `nuances_politiques.csv`
- `indicateurs_2012_2022.csv`
- Les fichiers de résultats électoraux détaillés (ex: `presidentielle_2022_tour1_par_commune.csv`).

Le script ETL (`src/etl/build_master.py`) est configuré pour lire tous les fichiers `*_par_commune.csv` et les combiner en un seul jeu de données pour l'entraînement.

## 2) Construire l'image Docker

```bash
docker compose build
```

## 3) Lancer l'ETL

Cela va créer le fichier `data/processed_csv/master_ml.csv`.

```bash
docker compose run --rm app src/etl/build_master.py --raw-dir data/raw_csv --out data/processed_csv/master_ml.csv
```

## 4) Entraîner les modèles

Les modèles sont entraînés sur toutes les années sauf la plus récente, qui est utilisée pour le test.

```bash
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv
```

Pour spécifier les années de test :

```bash
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv --test-years 2020 2022
```

## 5) Consulter les résultats

Les sorties sont générées dans le dossier `reports/` :
- `metrics.csv`: F1-score et accuracy pour chaque modèle.
- `figures/cm_*.png`: Matrices de confusion.
- `classification_report_*.txt`: Rapports de classification détaillés.