# MSPR Nantes — POC prédiction parti en tête (Docker & Compose)

## Prérequis
- Docker + Docker Compose v2

## Arborescence
data/
  raw_csv/          # dépose ici tes CSV bruts (pack robuste)
  processed_csv/    # sera rempli par l'ETL (master_ml.csv)
reports/
  figures/          # matrices de confusion, etc.
src/
  etl/build_master.py
  models/train.py
  common/io.py
docker-compose.yml
Dockerfile
requirements.txt
docs/

## 1) Préparer les données
Dépose dans `data/raw_csv/` au minimum :
- communes_nantes_metropole.csv
- nuances_politiques.csv
- indicateurs_2012_2022.csv
- Les fichiers de résultats électoraux détaillés (ex: `presidentielle_2022_tour1_par_commune.csv`). Le script ETL est maintenant conçu pour utiliser ces fichiers et ignorera le fichier `elections_master_2012_2022.csv` s'il est présent.

## 2) Construire l'image
docker compose build

## 3) Lancer l'ETL → master_ml.csv
docker compose run --rm app src/etl/build_master.py --raw-dir data/raw_csv --out data/processed_csv/master_ml.csv

Le script ETL a été amélioré pour :
- Utiliser les fichiers de résultats détaillés (`*_par_commune.csv`) pour des données plus précises.
- Calculer automatiquement le parti en tête (`parti_en_tete`) à partir des résultats.
- Gérer les valeurs manquantes dans les données.

## 4) Entraîner les modèles
# Test par défaut: dernière année
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv

# Spécifier des années de test (ex: 2020 et 2022)
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv --test-years 2020 2022

## Sorties
- data/processed_csv/master_ml.csv
- reports/metrics.csv
- reports/figures/cm_logreg.png, cm_rf.png
- reports/classification_report_*.txt

Notes: 
- Les lignes avec estime=true sont exclues par défaut à l'entraînement.
- Les deltas sont calculés par commune & type_scrutin quand les colonnes existent.


---
## Raccourcis Makefile
- Construire l'image : `make build`
- ETL : `make etl`
- Train : `make train` ou `make train TEST_YEARS="2020 2022"`
- Tout enchaîner : `make all`

## Pipeline en une commande
### Option A — script hôte
- `./scripts/pipeline.sh` (test par défaut : dernière année)
- `./scripts/pipeline.sh 2020 2022` (spécifie les années de test)

### Option B — service Compose dédié
- Par défaut (test sur dernière année) :
  ```bash
  docker compose -f docker-compose.pipeline.yml up --build
  ```
- Avec des années de test personnalisées :
  ```bash
  TEST_YEARS="2020 2022" docker compose -f docker-compose.pipeline.yml up --build
  ```


## Cartes (GeoJSON)

- Récupérer le GeoJSON des communes :

  ```bash

  docker compose run --rm app python src/etl/fetch_geojson.py

  ```

- Puis ouvrir `notebooks/02_eda_full.ipynb` → section **7) Carte**.

- Voir `docs/README_MAPS.md` pour les détails et le dépannage.



## Exporter une carte (PNG)

- Récupérer d'abord le GeoJSON si besoin :

  ```bash

  docker compose run --rm app python src/etl/fetch_geojson.py

  ```

- Exporter une carte :

  ```bash

  make map YEAR=2022 SCRUTIN=presidentielle TOUR=1 OUT=reports/figures/map_2022_pres_t1.png

  ```

  ou directement :

  ```bash

  docker compose run --rm app python src/etl/export_map.py --year 2022 --scrutin presidentielle --tour 1 --out reports/figures/map_2022_pres_t1.png

  ```