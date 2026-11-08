# U04.E07 · Evaluación de impacto y auditoría de equidad

**INF-8239 Ciencia de Datos II** · Unidad 04 · Ética y roles en Ciencia de Datos
Estudiante: Melvin H. Rivas Genao · Matrícula 100279298 · Docente: Edwin Ramón José Nolasco

Expediente que integra LAB11 (evaluación de impacto ético) y LAB12 (auditoría de equidad con
Fairlearn) sobre el proyecto base del curso `INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv`.
El sistema es un DSS sintético que **sugiere el orden de revisión humana** de casos territoriales.
Los datos son sintéticos y didácticos, y el sistema no autoriza decisiones automáticas sobre personas.

## Decisión: **LIMITAR**

Piloto acotado con la regresión logística del curso, sólo como orden sugerido. Todos los casos se
revisan, no se usa el grupo protegido al decidir, hay apelación, monitoreo mensual de brechas con IC
y condición de retiro. Detalle en [`reports/lab11/DECISION_RECORD.md`](reports/lab11/DECISION_RECORD.md).

| Candidato (prueba, 160 casos) | Recall | Brecha recall [IC 95 %] | Brecha FPR [IC 95 %] | Puertas del curso | Con IC superior |
|---|---|---|---|---|---|
| **Logística (baseline)** | 0.717 | 0.138 [0.010, 0.318] | 0.125 [0.006, 0.398] | ✔ | ✘ |
| Árbol | 0.717 | 0.181 | 0.168 | ✘ | ✘ |
| Logística sin `zone` | 0.707 | 0.114 | 0.327 | ✘ | ✘ |
| Regla transparente (no predictiva) | 0.837 | 0.131 | 0.106 | ✔ | ✘ |
| Logística, umbral 0.56 (validación) | 0.696 | 0.135 | 0.077 | ✔ | ✘ |
| ExponentiatedGradient | 0.772 | 0.079 | 0.212 | ✘ | ✘ |
| ThresholdOptimizer (usa el grupo al decidir) | 0.804 | 0.069 | 0.168 | ✘ | ✘ (excluido) |

Fuente: `reports/e07/candidates.csv` y `gates.csv`. Las puertas son las de `configs/governance.yml`:
recall ≥ 0.68 y brechas ≤ 0.16. Valores elegidos por el estudiante: daño prioritario = falso
negativo; métrica principal = brecha de recall; tolerancia = 0.16 con monitoreo del IC.

## Inicio rápido

```bash
uv sync --frozen
uv run pytest -q                                   # 24 pruebas (10 del curso + 14 del expediente)
uv run python scripts/check_environment.py
uv run python scripts/lab11_impact.py              # LAB11: valida insumos y puntúa riesgos
uv run python scripts/lab12_audit.py --model logistic
uv run python scripts/lab12_audit.py --model tree
uv run python scripts/validate_lab12_decision.py
uv run python scripts/e07_audit.py                 # E07: IC, interseccionalidad, mitigación, puertas, NIST
```

## Artefactos editables

| Requisito | Archivo |
|---|---|
| Finalidad, usuarios, afectados, alternativa no predictiva, uso prohibido, retiro y apelación | `student_inputs/lab11_impact.yml` |
| Interesados: beneficio, daño, poder y participación | `student_inputs/stakeholders.csv` |
| Registro de 11 riesgos con control, responsable, evidencia, residual, función NIST y tipo de norma | `student_inputs/risk_register.csv` |
| RACI | `student_inputs/raci.csv` |
| Decisión LAB12: daño, métrica, tolerancia, evidencia, limitación y recomendación | `student_inputs/lab12_decision.yml` |
| Obligación legal, marco voluntario y recomendación ética | `docs/NORMATIVE_MATRIX.csv` |
| Registro de decisión | `reports/lab11/DECISION_RECORD.md` |
| Model Card, Dataset Card y declaración de IA | `docs/` |
| Evidencia generada | `reports/lab11/`, `reports/lab12/{logistic,tree}/`, `reports/e07/` |

## Cambios respecto al proyecto base

* **`scripts/lab11_impact.py`.** Se corrigió un `SyntaxError` del original. Además, ya no sobrescribe
  el registro de decisión.
* **Archivos nuevos.** `src/inf8239_u04/audit_extra.py`, `scripts/e07_audit.py` y
  `tests/test_e07.py`.
* **Dependencia añadida.** `matplotlib`, para la figura de brechas.

El resto del proyecto base no se modificó. Las 10 pruebas del curso siguen en verde.

## Uso de IA

Se usó Claude (Anthropic). Ver [`docs/AI_USE_DECLARATION.md`](docs/AI_USE_DECLARATION.md). Los valores
del análisis los decidió el estudiante, que responde por las referencias, la interpretación normativa,
el código y las conclusiones.
