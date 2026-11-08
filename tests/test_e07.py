"""Pruebas del expediente U04.E07: auditoría extendida e insumos del estudiante."""
import ast
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from inf8239_u04.audit_extra import (RuleBaseline, bootstrap_gaps, compare_candidates, gate_check, group_gaps,
                                     support_flags, threshold_for_recall)
from inf8239_u04.data import features, load_data, temporal_split
from inf8239_u04.impact import score_risks, validate_impact

ROOT = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ métricas
def test_group_gaps_known_values():
    y = np.array([1, 1, 0, 0, 1, 1, 0, 0])
    p = np.array([1, 0, 0, 0, 1, 1, 1, 0])
    s = np.array(["A"] * 4 + ["B"] * 4)
    g = group_gaps(y, p, s)
    assert g["recall_gap"] == pytest.approx(0.5)      # A 0.5, B 1.0
    assert g["fpr_gap"] == pytest.approx(0.5)         # A 0.0, B 0.5
    assert g["selection_rate_gap"] == pytest.approx(0.5)


def test_bootstrap_interval_contains_point_estimate():
    rng = np.random.default_rng(0)
    y = rng.integers(0, 2, 300)
    s = np.where(rng.random(300) < 0.4, "G2", "G1")
    p = np.where(s == "G1", y * (rng.random(300) < 0.6), y * (rng.random(300) < 0.85)).astype(int)
    ci = bootstrap_gaps(y, p, s, n_boot=300, seed=1).set_index("brecha")
    r = ci.loc["recall_gap"]
    assert r.ic95_inf <= r.estimacion <= r.ic95_sup


def test_support_flags_mark_small_groups():
    y = np.array([1] * 30 + [0] * 30 + [1] * 3 + [0] * 3)
    s = np.array(["grande"] * 60 + ["chico"] * 6)
    t = support_flags(y, s)
    assert t.loc["grande", "recall_interpretable"] and not t.loc["chico", "recall_interpretable"]
    assert "soporte insuficiente" in t.loc["chico", "advertencia"]


def test_rule_baseline_is_transparent():
    X = pd.DataFrame({"previous_incidents": [0, 1, 2, 3, 4, 5]})
    r = RuleBaseline().fit(X)
    assert r.k_ == 2.5 and list(r.predict(X)) == [0, 0, 0, 1, 1, 1]


def test_threshold_for_recall_reaches_target():
    y = np.array([1, 1, 1, 1, 0, 0, 0, 0])
    proba = np.array([0.9, 0.8, 0.6, 0.3, 0.7, 0.2, 0.1, 0.05])
    t = threshold_for_recall(y, proba, target=0.75)
    assert ((proba >= t) & (y == 1)).sum() / 4 >= 0.75


def test_gate_rejects_use_of_protected_attribute():
    row = pd.Series({"recall": 0.9, "recall_gap": 0.0, "fpr_gap": 0.0, "latencia_ms": 1, "kb_modelo": 1,
                     "recall_gap_ic_sup": 0.0, "fpr_gap_ic_sup": 0.0, "usa_atributo_al_decidir": True})
    gates = {"min_recall": 0.68, "max_recall_gap": 0.16, "max_fpr_gap": 0.16, "max_latency_ms": 500, "max_model_kb": 1024}
    assert gate_check(row, gates)["sin_atributo_al_decidir"] is False


def test_protected_attribute_never_enters_model():
    assert "protected_group" not in features(load_data()).columns


def test_candidates_flag_threshold_optimizer_only():
    tr, te = temporal_split(load_data())
    res, by, info = compare_candidates(tr, te, n_boot=50)
    flagged = res[res.usa_atributo_al_decidir].candidato.tolist()
    assert len(flagged) == 1 and flagged[0].startswith("ThresholdOptimizer")
    assert 0.05 <= info["umbral_validacion"] <= 0.95 and len(res) == 7


# ------------------------------------------------------------------ insumos del estudiante
def test_impact_assessment_complete():
    data = yaml.safe_load((ROOT / "student_inputs/lab11_impact.yml").read_text(encoding="utf-8"))
    assert validate_impact(data)
    assert "0.16" in data["withdrawal_condition"]


def test_risk_register_complete_and_traceable():
    r = score_risks(pd.read_csv(ROOT / "student_inputs/risk_register.csv"))
    assert len(r) >= 8 and r.id.is_unique
    assert r.likelihood_1_4.between(1, 4).all() and r.impact_1_4.between(1, 4).all()
    assert set(r.residual) <= {"low", "medium", "high"}
    critical = r[r.priority >= 8]
    assert (critical.owner.str.len() > 0).all() and (critical.evidence.str.len() > 0).all()
    assert r.nist_ai_rmf.notna().all()


def test_stakeholders_complete():
    s = pd.read_csv(ROOT / "student_inputs/stakeholders.csv")
    assert not s.astype(str).apply(lambda c: c.str.contains("REPLACE")).any().any()
    assert set(s.power) <= {"low", "medium", "high"} and len(s) >= 4


def test_decision_is_explicit():
    d = yaml.safe_load((ROOT / "student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
    assert all(str(v).strip() not in {"", "REPLACE"} for v in d.values())
    assert d["recommendation"].split(".")[0].strip() in {"DESPLEGAR", "MODIFICAR", "LIMITAR", "NO UTILIZAR"}


def test_normative_matrix_distinguishes_three_types():
    m = pd.read_csv(ROOT / "docs/NORMATIVE_MATRIX.csv")
    assert set(m.tipo) == {"obligación legal", "marco voluntario", "recomendación ética"}
    cond = m[m.vinculante_en_este_caso == "condicional"]
    assert (cond.condicion.str.len() > 10).all()


def test_course_lab11_script_compiles():
    ast.parse((ROOT / "scripts/lab11_impact.py").read_text(encoding="utf-8"))
