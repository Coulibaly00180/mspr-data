import os
import pandas as pd

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def read_csv_safe(path: str, **kwargs) -> pd.DataFrame:
    for enc in ("utf-8", "latin-1"):
        try:
            return pd.read_csv(path, encoding=enc, **kwargs)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(path, **kwargs)

def write_csv_safe(df: pd.DataFrame, path: str, index: bool=False) -> None:
    df.to_csv(path, index=index, encoding="utf-8")

def cols_like(df, prefixes):
    return [c for c in df.columns if any(c.startswith(p) for p in prefixes)]
