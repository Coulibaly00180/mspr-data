# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a machine learning project for predicting electoral winners in the Nantes metropolitan area. It's a Dockerized Python application that performs ETL operations on electoral and socio-economic data, then trains multiple classification models to predict which political party will lead in each commune.

## Essential Commands

### Building and Running the Application
```bash
# Build Docker image
make build
# or
docker compose build

# Run full pipeline (ETL + Training)
make all

# Run ETL only (creates master_ml.csv)
make etl
# or
docker compose run --rm app src/etl/build_master.py --raw-dir data/raw_csv --out data/processed_csv/master_ml.csv

# Train models (uses last year for testing by default)
make train
# or
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv

# Train with specific test years
make train TEST_YEARS="2020 2022"
# or
docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv --test-years 2020 2022
```

### Pipeline Shortcuts
```bash
# Host script approach
./scripts/pipeline.sh                    # Test on last year
./scripts/pipeline.sh 2020 2022         # Test on specific years

# Docker Compose service approach
docker compose -f docker-compose.pipeline.yml up --build
TEST_YEARS="2020 2022" docker compose -f docker-compose.pipeline.yml up --build
```

### Geographic Data and Maps
```bash
# Fetch GeoJSON data for communes
docker compose run --rm app python src/etl/fetch_geojson.py

# Generate a PNG map
make map YEAR=2022 SCRUTIN=presidentielle TOUR=1 OUT=reports/figures/map_2022_pres_t1.png
# or
docker compose run --rm app python src/etl/export_map.py --year 2022 --scrutin presidentielle --tour 1 --out reports/figures/map_2022_pres_t1.png
```

### Visualization and Analysis
```bash
# Generate all visualizations and analysis
make viz

# Individual analysis modules
make audit                # Data quality audit
make trends              # Trend analysis graphs  
make interactive         # Interactive dashboard
make geographic          # Geographic/map analysis

# Direct script execution
docker compose run --rm app src/viz/run_all_visualizations.py
docker compose run --rm app src/audit_winner.py
```

### Data Management
```bash
# Clean generated files
make clean
```

## Architecture

### Core Components

1. **ETL Pipeline** (`src/etl/build_master.py`): 
   - Loads and consolidates electoral data from `*_par_commune.csv` files
   - Merges with socio-economic indicators
   - Calculates features (participation rates, deltas, previous winners)
   - Outputs `data/processed_csv/master_ml.csv`

2. **Model Training** (`src/models/train.py`):
   - Trains 4 classification models: Logistic Regression, Random Forest, SVM, XGBoost
   - Uses temporal split (train on earlier years, test on specified years)
   - Outputs metrics, confusion matrices, and classification reports

3. **Common Utilities** (`src/common/io.py`):
   - Safe CSV reading with encoding detection
   - Directory creation helpers

### Data Flow

1. **Raw Data** (`data/raw_csv/`): Electoral results and socio-economic indicators
2. **ETL Processing**: Consolidation, feature engineering, normalization
3. **Master Dataset** (`data/processed_csv/master_ml.csv`): ML-ready dataset
4. **Model Training**: Temporal train/test split and evaluation
5. **Reports** (`reports/`): Metrics, figures, classification reports

### Key Features Engineering

- **Temporal Features**: Previous election winners, year-over-year deltas
- **Participation Metrics**: Turnout rates, blank/null vote percentages
- **Party Standardization**: Maps candidate names to political families
- **Geographic Integration**: Commune-level socio-economic indicators

### Model Evaluation Strategy

- **Temporal Split**: Training on historical data, testing on recent years
- **Class Balancing**: Uses balanced class weights for imbalanced data
- **Multi-Model Approach**: Compares Logistic Regression, Random Forest, SVM, XGBoost
- **Comprehensive Metrics**: Accuracy, F1-macro, confusion matrices, classification reports

## Data Requirements

Place these files in `data/raw_csv/`:
- `communes_nantes_metropole.csv`: Reference communes data
- `nuances_politiques.csv`: Political party mappings
- `indicateurs_2012_2022.csv`: Socio-economic indicators
- `*_par_commune.csv`: Detailed electoral results (prioritized over master files)

## Output Structure

- `reports/metrics.csv`: Model performance comparison
- `reports/figures/cm_*.png`: Confusion matrices for each model
- `reports/classification_report_*.txt`: Detailed classification reports
- `reports/feature_importances_rf.csv`: Random Forest feature importance rankings

## Development Notes

- The application is designed to run entirely in Docker containers
- ETL handles missing data and encoding issues automatically
- Models use cross-validation and balanced class weights
- Geographic visualization requires GeoJSON data fetching
- All paths are containerized (`/app/` prefix in containers)