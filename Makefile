.PHONY: build etl train all clean viz audit trends interactive geographic

build:
	docker compose build

# Build master_ml.csv from raw CSVs
etl:
	docker compose run --rm app src/etl/build_master.py --raw-dir data/raw_csv --out data/processed_csv/master_ml.csv

# Train models; optional TEST_YEARS="2020 2022"
train:
	@if [ -n "$(TEST_YEARS)" ]; then \    		docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv --test-years $(TEST_YEARS); \    	else \    		docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv; \    	fi

# Run full pipeline: ETL then Train
all: etl train

clean:
	rm -f data/processed_csv/master_ml.csv
	rm -f reports/metrics.csv reports/classification_report_*.txt
	rm -f reports/figures/cm_*.png


# Export a PNG map: make map YEAR=2022 SCRUTIN=presidentielle TOUR=1 OUT=reports/figures/map_2022_pres_t1.png
map:
	@if [ -z "$(YEAR)" ]; then echo "Please provide YEAR (e.g., YEAR=2022)"; exit 2; fi
	@if [ ! -f data/geo/communes_nantes_metropole.geojson ]; then \

		docker compose run --rm app python src/etl/fetch_geojson.py; \

	fi

	@if [ -z "$(SCRUTIN)" ]; then export SCRUTIN=presidentielle; else export SCRUTIN=$(SCRUTIN); fi; \

	if [ -z "$(TOUR)" ]; then export TOUR=1; else export TOUR=$(TOUR); fi; \

	if [ -z "$(OUT)" ]; then export OUT=reports/figures/map_parti_en_tete.png; else export OUT=$(OUT); fi; \

	docker compose run --rm app python src/etl/export_map.py --year $(YEAR) --scrutin $$SCRUTIN --tour $$TOUR --out $$OUT

# Generate all visualizations and analysis
viz:
	docker compose run --rm app src/viz/run_all_visualizations.py

# Run data quality audit
audit:
	docker compose run --rm app src/audit_winner.py

# Generate trend analysis only
trends:
	docker compose run --rm app src/viz/trends_analyzer.py --data data/processed_csv/master_ml.csv --output reports/trends

# Generate interactive dashboard only  
interactive:
	docker compose run --rm app src/viz/interactive_dashboard.py --data data/processed_csv/master_ml.csv --output reports/interactive

# Generate geographic analysis only
geographic:
	@if [ ! -f data/geo/communes_nantes_metropole.geojson ]; then \
		docker compose run --rm app python src/etl/fetch_geojson.py; \
	fi
	docker compose run --rm app src/viz/geographic_analyzer.py --data data/processed_csv/master_ml.csv --output reports/geographic --all-elections
