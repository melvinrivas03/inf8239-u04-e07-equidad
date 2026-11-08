# Model Card · Territorial Review DSS (sintético) · regresión logística del curso

> Completada en U04.E07 (LAB11–LAB12). LAB13 añadirá gobernanza operativa y la aplicación.

## Intended use
Sugerir el **orden de revisión humana** de casos territoriales sintéticos. Es apoyo a la decisión: un
analista revisa y firma cada caso, y ningún caso se descarta. Decisión vigente: **LIMITAR**, es decir,
piloto acotado (ver `reports/lab11/DECISION_RECORD.md`).

## Out-of-scope use
* Intervención automática, decisión de elegibilidad y declaración de emergencia
  (`configs/governance.yml`).
* Usar el grupo protegido para decidir; perfilar personas o zonas.
* Usar el sistema con datos reales sin una nueva evaluación de impacto. Si lo opera una entidad
  pública, eso incluye la evaluación de impacto ético y de derechos del Decreto 787-26.

## Data and split
* `data/territorial_risk_synthetic.csv`: 640 casos sintéticos, con una tasa positiva de 0.552.
* Grupos: G1 con 396 casos (tasa base 0.497) y G2 con 244 (tasa base 0.639).
* **Corte temporal**: entrenamiento hasta el 24-09-2026 (480 casos) y prueba desde el 25-09-2026
  (160 casos: 101 de G1 y 59 de G2).
* Variables del modelo: `zone`, `age_band`, `previous_incidents`, `infrastructure_score` y
  `exposure`.
* `protected_group` se **excluye del modelo** y sólo se usa para auditar.

## Global and subgroup evaluation (prueba)
| Métrica | Global | G1 | G2 | Brecha [IC 95 %] |
|---|---|---|---|---|
| Recall | 0.717 | 0.653 | 0.791 | 0.138 [0.010, 0.318] |
| FPR | 0.279 | 0.250 | 0.375 | 0.125 [0.006, 0.398] |
| Tasa de selección | 0.531 | 0.446 | 0.678 | 0.232 |
| Accuracy | 0.719 | 0.703 | 0.746 | — |

La auditoría interseccional (grupo × banda de edad) está en `reports/e07/intersectional_baseline.csv`.
4 de las 8 intersecciones no tienen soporte suficiente (n < 20, o menos de 5 positivos o negativos):
se reportan, pero no se interpretan como brechas. La comparación con otros 6 candidatos está en
`reports/e07/candidates.csv`.

## Green AI evidence
* Logística: 3.6 KB, entrenamiento en unos 0.02 s, unos 0.02 ms por caso.
* El árbol ocupa el doble (7.9 KB), no mejora el recall y falla las dos puertas de brecha.
* ExponentiatedGradient ocupa 135 KB y empeora la brecha de FPR.

Se elige la opción suficiente.

## Limitations, human oversight and appeal
* Datos sintéticos: sin validez externa.
* Muestra de prueba pequeña: los intervalos son amplios.
* Tasas base distintas: las tasas de error no pueden igualarse todas a la vez.
* Una brecha no prueba discriminación causal.
* Supervisión humana en todos los casos, con revisión aleatoria del 5 % de los casos de baja prioridad.
* Apelación ante un revisor distinto en 5 días hábiles.
* Condición de retiro definida en el registro de decisión.

## Owner and review date
Institutional Owner (A) y Data Scientist (R de validación del modelo). Expediente preparado por
Melvin H. Rivas Genao el 8 de noviembre de 2026. La próxima revisión es al cerrar la primera ventana
mensual del piloto.
