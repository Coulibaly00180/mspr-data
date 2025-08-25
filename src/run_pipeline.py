import os, shlex, subprocess, sys
# Read TEST_YEARS env (space-separated) if provided
test_years = os.environ.get("TEST_YEARS", "").strip()
etl_cmd = ["python","/app/src/etl/build_master.py","--raw-dir","/app/data/raw_csv","--out","/app/data/processed_csv/master_ml.csv"]
train_cmd = ["python","/app/src/models/train.py","--data","/app/data/processed_csv/master_ml.csv"]
if test_years:
    train_cmd += ["--test-years", *shlex.split(test_years)]
print("[run_pipeline] ETL:", " ".join(etl_cmd), flush=True)
subprocess.check_call(etl_cmd)
print("[run_pipeline] TRAIN:", " ".join(train_cmd), flush=True)
subprocess.check_call(train_cmd)
