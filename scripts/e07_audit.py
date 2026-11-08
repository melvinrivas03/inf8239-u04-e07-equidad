"""U04.E07 · Auditoría completa: candidatos, incertidumbre, interseccionalidad, puertas y NIST AI RMF.

    uv run python scripts/e07_audit.py

Escribe todo en reports/e07/. No modifica los insumos del estudiante; los valida.
"""
import json
import platform
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import yaml  # noqa: E402

from inf8239_u04.audit_extra import (bootstrap_gaps, compare_candidates, gate_check,  # noqa: E402
                                     intersectional_report, support_flags)
from inf8239_u04.data import features, load_data, temporal_split  # noqa: E402
from inf8239_u04.governance import load_config, validate_raci  # noqa: E402
from inf8239_u04.impact import score_risks, validate_impact  # noqa: E402
from inf8239_u04.model import build_model  # noqa: E402

OUT = Path("reports/e07")
OUT.mkdir(parents=True, exist_ok=True)
SEED, N_BOOT = 42, 2000

cfg = load_config()
gates = cfg["gates"]
decision = yaml.safe_load(Path("student_inputs/lab12_decision.yml").read_text(encoding="utf-8"))
impact = yaml.safe_load(Path("student_inputs/lab11_impact.yml").read_text(encoding="utf-8"))
validate_impact(impact)
risks = score_risks(pd.read_csv("student_inputs/risk_register.csv"))
validate_raci(pd.read_csv("student_inputs/raci.csv"))
norm = pd.read_csv("docs/NORMATIVE_MATRIX.csv")

df = load_data()
train, test = temporal_split(df)

# 1. descripción y soporte
desc = {
    "filas": len(df), "positivos_pct": float(df.target.mean()),
    "tasa_base_por_grupo": df.groupby("protected_group").target.mean().round(4).to_dict(),
    "n_por_grupo": df.protected_group.value_counts().to_dict(),
    "train_hasta": str(train.received_date.max().date()), "test_desde": str(test.received_date.min().date()),
    "n_train": len(train), "n_test": len(test),
    "test_por_grupo": test.protected_group.value_counts().to_dict(),
    "variables_modelo": list(features(df).columns),
    "excluidas_del_modelo": ["case_id", "received_date", "protected_group", "target"],
}
(OUT / "dataset_summary.json").write_text(json.dumps(desc, indent=2, ensure_ascii=False), encoding="utf-8")
support_flags(test.target, test.protected_group).to_csv(OUT / "support_groups.csv")

# 2. candidatos (global, por grupo, IC, costo)
res, by_groups, info = compare_candidates(train, test, recall_target=0.80, n_boot=N_BOOT, seed=SEED)
res.round(5).to_csv(OUT / "candidates.csv", index=False)
long = pd.concat({k: v for k, v in by_groups.items()}, names=["candidato", "grupo"]).reset_index()
long.round(5).to_csv(OUT / "by_group_all_candidates.csv", index=False)
gate_rows = []
for _, r in res.iterrows():
    g = gate_check(r, gates)
    gate_rows.append({"candidato": r.candidato, **g, "cumple_puertas_curso": all(g[k] for k in
                      ("recall", "recall_gap", "fpr_gap", "latency", "model_size")),
                      "cumple_con_ic_superior": all(g.values())})
gates_df = pd.DataFrame(gate_rows)
gates_df.to_csv(OUT / "gates.csv", index=False)

# 3. baseline: IC de brechas e interseccionalidad
base = build_model("logistic").fit(features(train), train.target)
pred = base.predict(features(test))
bootstrap_gaps(test.target, pred, test.protected_group, N_BOOT, SEED).round(5).to_csv(OUT / "bootstrap_gaps_baseline.csv", index=False)
inter = intersectional_report(test, pred)
inter.round(5).to_csv(OUT / "intersectional_baseline.csv")

# 4. figura: compromiso utilidad / brechas con IC
fig, axes = plt.subplots(1, 2, figsize=(10, 3.9), sharey=True)
short = lambda s: re.sub(r"\s*\(.*\)", "", s).replace("Logística, umbral", "Umbral")  # noqa: E731
colors = ["#1f6feb" if not u else "#cf222e" for u in res.usa_atributo_al_decidir]
for ax, gap, lo_hi in ((axes[0], "recall_gap", "recall_gap_ic95"), (axes[1], "fpr_gap", "fpr_gap_ic95")):
    lo = res[lo_hi].str.extract(r"\[([\d.]+), ([\d.]+)\]").astype(float)
    y = np.arange(len(res))
    ax.errorbar(res[gap], y, xerr=[res[gap] - lo[0], lo[1] - res[gap]], fmt="none", ecolor="#8c959f", capsize=3)
    ax.scatter(res[gap], y, c=colors, zorder=3)
    tol = gates["max_recall_gap"] if gap == "recall_gap" else gates["max_fpr_gap"]
    ax.axvline(tol, color="#d29922", ls="--", lw=1, label=f"tolerancia {tol}")
    ax.set_xlabel(f"brecha de {'recall' if gap == 'recall_gap' else 'FPR'} entre G1 y G2 (IC 95 %)")
    ax.legend(frameon=False, fontsize=7, loc="lower right")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
axes[0].set_yticks(np.arange(len(res)))
axes[0].set_yticklabels([f"{short(c)}  (recall {r:.2f})" for c, r in zip(res.candidato, res.recall)], fontsize=7)
axes[0].invert_yaxis()
fig.suptitle("Brechas por grupo con incertidumbre (rojo = usa el grupo protegido al decidir)", fontsize=9)
fig.tight_layout()
fig.savefig(OUT / "tradeoff_gaps.png", dpi=150)
plt.close(fig)

# 5. NIST AI RMF: evidencia por función (archivo presente ≠ control eficaz)
def present(p):
    return Path(p).exists()


rmf = {
    "GOVERN": {"acciones": ["propietario y RACI definidos", "usos prohibidos en configuración", "matriz normativa",
                            "declaración de uso de IA"],
               "evidencia": ["student_inputs/raci.csv", "configs/governance.yml", "docs/NORMATIVE_MATRIX.csv",
                             "docs/AI_USE_DECLARATION.md"]},
    "MAP": {"acciones": ["finalidad, usuarios, afectados y alternativa no predictiva", "interesados con poder y daño",
                         f"{len(risks)} riesgos con escenario, control y responsable"],
            "evidencia": ["student_inputs/lab11_impact.yml", "student_inputs/stakeholders.csv",
                          "student_inputs/risk_register.csv"]},
    "MEASURE": {"acciones": ["métricas globales, por grupo e interseccionales con soporte",
                             "IC 95 % por bootstrap de las brechas", "7 candidatos con costo"],
                "evidencia": ["reports/e07/candidates.csv", "reports/e07/bootstrap_gaps_baseline.csv",
                              "reports/e07/intersectional_baseline.csv", "reports/e07/gates.csv"]},
    "MANAGE": {"acciones": ["decisión LIMITAR con condiciones", "condición de retiro y apelación",
                            "monitoreo de brechas por ventanas"],
               "evidencia": ["student_inputs/lab12_decision.yml", "reports/lab11/DECISION_RECORD.md"]},
}
for k, v in rmf.items():
    v["archivos_presentes"] = all(present(p) for p in v["evidencia"])
    v["advertencia"] = "La presencia de archivos no demuestra que el control sea eficaz; ver pruebas y piloto."
(OUT / "rmf_summary.json").write_text(json.dumps(rmf, indent=2, ensure_ascii=False), encoding="utf-8")

# 6. decisión trazable
summary = {
    "decision_estudiante": decision,
    "candidato_recomendado": res.iloc[0].candidato,
    "puertas": gates,
    "baseline": {k: (float(res.iloc[0][k]) if isinstance(res.iloc[0][k], (float, np.floating, int)) else res.iloc[0][k])
                 for k in ("recall", "recall_G1", "recall_G2", "recall_gap", "recall_gap_ic95", "fpr_gap", "fpr_gap_ic95",
                           "kb_modelo", "latencia_ms")},
    "cumple_puertas_curso": bool(gates_df.iloc[0].cumple_puertas_curso),
    "cumple_con_ic_superior": bool(gates_df.iloc[0].cumple_con_ic_superior),
    "intersecciones_sin_soporte": int((inter.advertencia != "").sum()),
    "intersecciones_total": int(len(inter)),
    "umbral_validacion": info["umbral_validacion"], "regla_k": info["regla_k"],
    "riesgos": len(risks), "riesgos_prioridad_8_o_mas": int((risks.priority >= 8).sum()),
    "normas_por_tipo": norm.tipo.value_counts().to_dict(),
    "entorno": {"python": platform.python_version()}, "semilla": SEED, "bootstrap": N_BOOT,
}
(OUT / "decision_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
print(res[["candidato", "recall", "recall_gap", "recall_gap_ic95", "fpr_gap", "fpr_gap_ic95"]].round(3).to_string(index=False))
print(gates_df[["candidato", "cumple_puertas_curso", "cumple_con_ic_superior"]].to_string(index=False))
print("intersecciones sin soporte:", summary["intersecciones_sin_soporte"], "de", summary["intersecciones_total"])
