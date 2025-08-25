#!/usr/bin/env sh
set -e
TEST_YEARS="$*"
echo "[Pipeline] Running ETL..."
docker compose run --rm app src/etl/build_master.py --raw-dir data/raw_csv --out data/processed_csv/master_ml.csv
echo "[Pipeline] Training..."
if [ -n "$TEST_YEARS" ]; then
  docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv --test-years $TEST_YEARS
else
  docker compose run --rm app src/models/train.py --data data/processed_csv/master_ml.csv
fi
echo "[Pipeline] Done."
