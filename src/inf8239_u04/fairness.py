import pandas as pd
from fairlearn.metrics import MetricFrame, count, false_positive_rate, selection_rate, true_positive_rate
from sklearn.metrics import accuracy_score, precision_score

METRICS={"count":count,"accuracy":accuracy_score,"selection_rate":selection_rate,"recall":true_positive_rate,"precision":lambda y,p:precision_score(y,p,zero_division=0),"fpr":false_positive_rate}

def audit(y_true, y_pred, sensitive):
    mf=MetricFrame(metrics=METRICS,y_true=y_true,y_pred=y_pred,sensitive_features=sensitive)
    return mf.overall, mf.by_group, mf.difference(method="between_groups")

def intersectional(df):
    return df[["protected_group","age_band"]].astype(str).agg(" | ".join,axis=1)

def gap(by_group, metric):
    values=pd.to_numeric(by_group[metric],errors="coerce").dropna()
    return float(values.max()-values.min()) if len(values) else 0.0
