from pathlib import Path
import pandas as pd

REQUIRED = {"case_id","received_date","zone","protected_group","age_band","previous_incidents","infrastructure_score","exposure","target"}
PROHIBITED = {"name","document_number","email","phone"}

def load_data(path="data/territorial_risk_synthetic.csv"):
    df = pd.read_csv(Path(path), parse_dates=["received_date"])
    validate_schema(df)
    return df.sort_values("received_date").reset_index(drop=True)

def validate_schema(df):
    missing = REQUIRED - set(df.columns)
    forbidden = PROHIBITED & {str(c).lower() for c in df.columns}
    if missing: raise ValueError(f"Missing columns: {sorted(missing)}")
    if forbidden: raise ValueError(f"Direct identifiers prohibited: {sorted(forbidden)}")
    if not set(df.target.unique()).issubset({0,1}): raise ValueError("target must be binary")

def temporal_split(df, test_fraction=.25):
    cut = int(len(df) * (1-test_fraction))
    return df.iloc[:cut].copy(), df.iloc[cut:].copy()

def features(df):
    return df[["zone","age_band","previous_incidents","infrastructure_score","exposure"]]
