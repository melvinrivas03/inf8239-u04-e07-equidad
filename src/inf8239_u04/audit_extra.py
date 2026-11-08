"""Extensiones de auditoría para U04.E07: incertidumbre, soporte mínimo y alternativas.

* ``bootstrap_gaps``: IC 95 % por bootstrap estratificado por grupo para las brechas de
  recall, FPR y tasa de selección. Una brecha puntual sin intervalo puede ser ruido.
* ``support_flags``: marca los grupos (o intersecciones) sin datos suficientes para interpretar
  recall (pocos positivos) o FPR (pocos negativos). No se ocultan: se reportan con advertencia.
* Candidatos: baseline logístico, árbol, regla transparente no predictiva, umbral recalibrado en
  validación temporal, ExponentiatedGradient (atributo sólo en entrenamiento) y ThresholdOptimizer
  (usa el atributo al decidir: se evalúa pero queda EXCLUIDO del despliegue por trato desigual).
"""
from __future__ import annotations

import io
import time

import joblib
import numpy as np
import pandas as pd
from fairlearn.postprocessing import ThresholdOptimizer
from fairlearn.reductions import EqualizedOdds, ExponentiatedGradient
from sklearn.metrics import accuracy_score, precision_score, recall_score

from .data import features
from .fairness import audit, gap, intersectional
from .model import build_model
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

GAP_METRICS = ("recall", "fpr", "selection_rate")


# ------------------------------------------------------------------ métricas por grupo
def _rates(y, p):
    y, p = np.asarray(y), np.asarray(p)
    pos, neg = y == 1, y == 0
    return {
        "recall": p[pos].mean() if pos.any() else np.nan,
        "fpr": p[neg].mean() if neg.any() else np.nan,
        "selection_rate": p.mean() if len(p) else np.nan,
    }


def group_gaps(y, p, s) -> dict:
    y, p, s = np.asarray(y), np.asarray(p), np.asarray(s)
    rates = {g: _rates(y[s == g], p[s == g]) for g in np.unique(s)}
    out = {}
    for m in GAP_METRICS:
        vals = [r[m] for r in rates.values() if not np.isnan(r[m])]
        out[f"{m}_gap"] = float(max(vals) - min(vals)) if len(vals) > 1 else 0.0
    return out


def bootstrap_gaps(y, p, s, n_boot: int = 2000, seed: int = 42) -> pd.DataFrame:
    """IC 95 % percentil de las brechas, remuestreando DENTRO de cada grupo (conserva tamaños)."""
    y, p, s = np.asarray(y), np.asarray(p), np.asarray(s)
    rng = np.random.default_rng(seed)
    idx_by_g = {g: np.flatnonzero(s == g) for g in np.unique(s)}
    draws = {k: [] for k in (f"{m}_gap" for m in GAP_METRICS)}
    for _ in range(n_boot):
        idx = np.concatenate([rng.choice(ix, len(ix), replace=True) for ix in idx_by_g.values()])
        for k, v in group_gaps(y[idx], p[idx], s[idx]).items():
            draws[k].append(v)
    point = group_gaps(y, p, s)
    return pd.DataFrame([{"brecha": k, "estimacion": point[k], "ic95_inf": float(np.percentile(v, 2.5)),
                          "ic95_sup": float(np.percentile(v, 97.5))} for k, v in draws.items()])


def support_flags(y, s, min_n: int = 20, min_class: int = 5) -> pd.DataFrame:
    """Soporte por grupo: n, positivos y negativos, y si cada métrica es interpretable."""
    df = pd.DataFrame({"y": np.asarray(y), "g": np.asarray(s)})
    t = df.groupby("g")["y"].agg(n="size", positivos="sum")
    t["negativos"] = t["n"] - t["positivos"]
    t["recall_interpretable"] = (t["n"] >= min_n) & (t["positivos"] >= min_class)
    t["fpr_interpretable"] = (t["n"] >= min_n) & (t["negativos"] >= min_class)
    t["advertencia"] = np.where(t.recall_interpretable & t.fpr_interpretable, "",
                                "soporte insuficiente: no interpretar como brecha; recolectar más datos")
    return t


def intersectional_report(test: pd.DataFrame, pred, min_n: int = 20, min_class: int = 5) -> pd.DataFrame:
    keys = intersectional(test)
    _, by, _ = audit(test.target, pred, keys)
    sup = support_flags(test.target, keys, min_n, min_class)
    out = by.join(sup[["positivos", "negativos", "recall_interpretable", "fpr_interpretable", "advertencia"]])
    out.index.name = "grupo"
    return out


# ------------------------------------------------------------------ candidatos
def temporal_validation_split(train: pd.DataFrame, frac: float = 0.2):
    cut = int(len(train) * (1 - frac))
    return train.iloc[:cut].copy(), train.iloc[cut:].copy()


def threshold_for_recall(y, proba, target: float) -> float:
    """Mayor umbral cuyo recall en validación alcanza el objetivo (menos alertas a igual detección)."""
    best = 0.5
    for t in np.round(np.arange(0.05, 0.96, 0.01), 2):
        if recall_score(y, (proba >= t).astype(int), zero_division=0) >= target:
            best = t
    return float(best)


def build_model_without_zone():
    """Misma logística del curso pero SIN la variable territorial ``zone`` (posible proxy de residencia)."""
    prep = ColumnTransformer([
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["age_band"]),
        ("num", StandardScaler(), ["previous_incidents", "infrastructure_score", "exposure"]),
    ])
    return make_pipeline(prep, LogisticRegression(max_iter=1200, class_weight="balanced", random_state=42))


class RuleBaseline:
    """Alternativa NO predictiva y transparente: priorizar si incidentes previos ≥ k (k = mediana de
    entrenamiento). Cualquier operador puede aplicarla y explicarla sin modelo."""

    def fit(self, X, y=None):
        self.k_ = float(np.median(X["previous_incidents"]))
        return self

    def predict(self, X):
        return (X["previous_incidents"] >= self.k_).astype(int).to_numpy()


def _size_kb(obj) -> float:
    buf = io.BytesIO()
    joblib.dump(obj, buf)
    return buf.tell() / 1024


def _evaluate(name, pred, test, fit_s, size_kb, latency_ms, uses_attr_at_inference, note, n_boot, seed):
    y, s = test.target.to_numpy(), test.protected_group.to_numpy()
    _, by, _ = audit(test.target, pred, test.protected_group)
    ci = bootstrap_gaps(y, pred, s, n_boot=n_boot, seed=seed).set_index("brecha")
    row = {
        "candidato": name,
        "accuracy": accuracy_score(y, pred), "recall": recall_score(y, pred, zero_division=0),
        "precision": precision_score(y, pred, zero_division=0), "selection_rate": float(np.mean(pred)),
        "fpr": float(pred[y == 0].mean()),
        "recall_G1": by.loc["G1", "recall"], "recall_G2": by.loc["G2", "recall"],
        "fpr_G1": by.loc["G1", "fpr"], "fpr_G2": by.loc["G2", "fpr"],
        "recall_gap": gap(by, "recall"), "recall_gap_ic95": f"[{ci.loc['recall_gap','ic95_inf']:.3f}, {ci.loc['recall_gap','ic95_sup']:.3f}]",
        "recall_gap_ic_sup": ci.loc["recall_gap", "ic95_sup"],
        "fpr_gap": gap(by, "fpr"), "fpr_gap_ic95": f"[{ci.loc['fpr_gap','ic95_inf']:.3f}, {ci.loc['fpr_gap','ic95_sup']:.3f}]",
        "fpr_gap_ic_sup": ci.loc["fpr_gap", "ic95_sup"],
        "selection_gap": gap(by, "selection_rate"),
        "seg_entrenamiento": fit_s, "kb_modelo": size_kb, "latencia_ms": latency_ms,
        "usa_atributo_al_decidir": uses_attr_at_inference, "nota": note,
    }
    return row, by


def compare_candidates(train: pd.DataFrame, test: pd.DataFrame, recall_target: float = 0.80,
                       n_boot: int = 2000, seed: int = 42) -> tuple[pd.DataFrame, dict, dict]:
    Xtr, ytr, Xte = features(train), train.target, features(test)
    rows, by_groups, info = [], {}, {}

    def timed_fit(obj, *a, **k):
        t0 = time.perf_counter(); obj.fit(*a, **k); return time.perf_counter() - t0

    def latency(fn):
        t0 = time.perf_counter(); out = fn(); return out, (time.perf_counter() - t0) * 1000 / len(test)

    # 1-2. modelos del curso
    for kind, label in (("logistic", "Logística (baseline del curso)"), ("tree", "Árbol (alternativa del curso)")):
        m = build_model(kind)
        fs = timed_fit(m, Xtr, ytr)
        pred, lat = latency(lambda: m.predict(Xte))
        r, by = _evaluate(label, pred, test, fs, _size_kb(m), lat, False, "umbral 0.5", n_boot, seed)
        rows.append(r); by_groups[label] = by
        if kind == "logistic":
            base_model = m

    # 2b. sin la variable territorial (proxy de residencia)
    m = build_model_without_zone()
    fs = timed_fit(m, Xtr, ytr)
    pred, lat = latency(lambda: m.predict(Xte))
    label = "Logística sin zona (sin proxy territorial)"
    r, by = _evaluate(label, pred, test, fs, _size_kb(m), lat, False, "excluye zone; umbral 0.5", n_boot, seed)
    rows.append(r); by_groups[label] = by

    # 3. alternativa no predictiva
    rule = RuleBaseline()
    fs = timed_fit(rule, Xtr, ytr)
    pred, lat = latency(lambda: rule.predict(Xte))
    label = "Regla transparente (no predictiva)"
    r, by = _evaluate(label, pred, test, fs, _size_kb(rule), lat, False,
                      f"incidentes previos ≥ {rule.k_:g}", n_boot, seed)
    rows.append(r); by_groups[label] = by
    info["regla_k"] = rule.k_

    # 4. umbral recalibrado en validación temporal (sin mirar prueba)
    fit_part, val_part = temporal_validation_split(train)
    m_val = build_model("logistic").fit(features(fit_part), fit_part.target)
    thr = threshold_for_recall(val_part.target, m_val.predict_proba(features(val_part))[:, 1], recall_target)
    info["umbral_validacion"] = thr
    proba, lat = latency(lambda: base_model.predict_proba(Xte)[:, 1])
    pred = (proba >= thr).astype(int)
    label = f"Logística, umbral {thr:.2f} (recall objetivo {recall_target:.2f} en validación)"
    r, by = _evaluate(label, pred, test, 0.0, _size_kb(base_model), lat, False,
                      "un único umbral para todos; elegido en validación temporal", n_boot, seed)
    rows.append(r); by_groups[label] = by

    # 5. ExponentiatedGradient: el atributo sólo se usa para entrenar
    prep_model = build_model("logistic")
    prep = prep_model.steps[0][1].fit(Xtr)
    eg = ExponentiatedGradient(prep_model.steps[1][1], constraints=EqualizedOdds(difference_bound=0.05))
    t0 = time.perf_counter()
    eg.fit(prep.transform(Xtr), ytr, sensitive_features=train.protected_group)
    fs = time.perf_counter() - t0
    pred, lat = latency(lambda: np.asarray(eg.predict(prep.transform(Xte), random_state=seed)).astype(int))
    label = "ExponentiatedGradient (odds igualadas, ε = 0.05)"
    r, by = _evaluate(label, pred, test, fs, _size_kb((prep, eg)), lat, False,
                      "atributo sólo en entrenamiento; predicción aleatorizada", n_boot, seed)
    rows.append(r); by_groups[label] = by

    # 6. ThresholdOptimizer: umbrales por grupo → necesita el atributo al decidir
    to = ThresholdOptimizer(estimator=build_model("logistic"), constraints="equalized_odds",
                            predict_method="predict_proba", prefit=False)
    t0 = time.perf_counter()
    to.fit(Xtr, ytr, sensitive_features=train.protected_group)
    fs = time.perf_counter() - t0
    pred, lat = latency(lambda: np.asarray(to.predict(Xte, sensitive_features=test.protected_group,
                                                      random_state=seed)).astype(int))
    label = "ThresholdOptimizer (umbrales por grupo)"
    r, by = _evaluate(label, pred, test, fs, _size_kb(to), lat, True,
                      "usa el grupo protegido AL DECIDIR: excluido del despliegue", n_boot, seed)
    rows.append(r); by_groups[label] = by

    return pd.DataFrame(rows), by_groups, info


def gate_check(row: pd.Series, gates: dict) -> dict:
    """Puertas del curso (configs/governance.yml) + versión conservadora con el IC superior."""
    return {
        "recall": row["recall"] >= gates["min_recall"],
        "recall_gap": row["recall_gap"] <= gates["max_recall_gap"],
        "fpr_gap": row["fpr_gap"] <= gates["max_fpr_gap"],
        "latency": row["latencia_ms"] <= gates["max_latency_ms"],
        "model_size": row["kb_modelo"] <= gates["max_model_kb"],
        "recall_gap_ic_sup": row["recall_gap_ic_sup"] <= gates["max_recall_gap"],
        "fpr_gap_ic_sup": row["fpr_gap_ic_sup"] <= gates["max_fpr_gap"],
        "sin_atributo_al_decidir": not row["usa_atributo_al_decidir"],
    }
