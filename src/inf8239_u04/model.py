import time
from pathlib import Path
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

def build_model(kind="logistic"):
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["zone","age_band"]),
        ("num", StandardScaler(), ["previous_incidents","infrastructure_score","exposure"]),
    ])
    estimator = LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42) if kind == "logistic" else DecisionTreeClassifier(max_depth=5, class_weight="balanced", random_state=42)
    return make_pipeline(prep, estimator)

def fit_measure(model, X, y, output="models/model.joblib"):
    start=time.perf_counter(); model.fit(X,y); seconds=time.perf_counter()-start
    path=Path(output); path.parent.mkdir(parents=True,exist_ok=True); joblib.dump(model,path)
    return {"training_seconds":seconds,"model_kb":path.stat().st_size/1024}
