import pandas as pd

REQUIRED_IMPACT={"purpose","assisted_decision","users","affected_population","owner","non_predictive_alternative","out_of_scope_use","withdrawal_condition","appeal_mechanism"}
REQUIRED_RISK={"id","scenario","affected","likelihood_1_4","impact_1_4","control","owner","evidence","residual"}

def validate_impact(data):
    missing=REQUIRED_IMPACT-set(data)
    incomplete=[k for k in REQUIRED_IMPACT if str(data.get(k,"" )).strip() in {"","REPLACE"}]
    if missing or incomplete: raise ValueError(f"Incomplete impact assessment: {sorted(missing|set(incomplete))}")
    return True

def score_risks(df):
    if REQUIRED_RISK-set(df.columns): raise ValueError("Risk register columns missing")
    text_cols=["scenario","affected","control","owner","evidence"]
    if (df[text_cols].fillna("").eq("REPLACE")|df[text_cols].fillna("").eq("")).any().any(): raise ValueError("Complete all risk fields")
    out=df.copy(); out["priority"]=out.likelihood_1_4.astype(int)*out.impact_1_4.astype(int)
    return out.sort_values(["priority","impact_1_4"],ascending=False)
