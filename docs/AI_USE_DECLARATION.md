# Declaración de uso de IA

**Estudiante:** Melvin H. Rivas Genao · Matrícula 100279298 · U04.E07 · 8 de noviembre de 2026.

**Herramienta:** Claude (Anthropic), modelo Claude Opus 5.5, en la aplicación Claude con un entorno de
ejecución en la nube. Los commits del repositorio la identifican como coautora.

**Finalidad:** estructura del expediente, código de auditoría extendida, pruebas, búsqueda y
verificación de fuentes normativas y bibliográficas, y borradores de redacción.

## Lo que decidió el estudiante, no la IA

La IA presentó la evidencia y opciones con sus consecuencias. El estudiante eligió:
* el **daño prioritario**: falso negativo;
* la **métrica principal**: recall por grupo y brecha de recall;
* la **tolerancia**: 0.16 sobre la estimación puntual, con monitoreo del IC 95 %;
* la **decisión final**: LIMITAR.

Esos valores están en `student_inputs/lab12_decision.yml`.

## Fragmentos afectados

| Archivo | Aporte de la IA | Revisión humana |
|---|---|---|
| `src/inf8239_u04/audit_extra.py`, `scripts/e07_audit.py` | Código nuevo: IC por bootstrap, soporte mínimo, 7 candidatos, puertas con IC, figura y resumen NIST | Ejecución, lectura y pruebas |
| `tests/test_e07.py` | 14 pruebas nuevas | Ejecutadas: 24 de 24 pasan |
| `student_inputs/*.yml`, `*.csv` | Borradores de redacción a partir del caso y la evidencia; R09–R11 y su puntuación propuestos por la IA | Validados por el estudiante; R01–R08 conservan la probabilidad e impacto de la plantilla del curso |
| `docs/NORMATIVE_MATRIX.csv` | Clasificación en obligación legal, marco voluntario y recomendación ética, con fuentes | Revisión de la interpretación normativa por el estudiante |
| `reports/lab11/DECISION_RECORD.md`, `docs/MODEL_CARD.md` | Redacción a partir de `reports/e07/` | Cifras contrastadas con los CSV |

## Prompts relevantes

1. Enunciado del Ejercicio 07 (propósito, mandato y rúbrica) junto con las guías de LAB11 y LAB12.
2. Entrega del proyecto base `INF8239_U04_Gobernanza_DSS_Proyecto_Base_uv.zip`.
3. Elección de daño, tolerancia y decisión entre opciones presentadas con su evidencia.

## Verificaciones

* `uv run pytest -q`: 24 pruebas en verde (10 del curso y 14 nuevas).
* `scripts/lab11_impact.py`, `scripts/validate_lab12_decision.py` y `scripts/e07_audit.py` se
  ejecutan sin errores.
* Las cifras de los documentos provienen de `reports/e07/*.csv` y `*.json`.
* Las fuentes normativas se buscaron en la web, con fecha de consulta 8 de noviembre de 2026:
  * Ley 172-13 y artículos 39, 44 y 70 de la Constitución: fuentes oficiales y jurisprudencia del TC.
  * Decreto 498-23 (ENIA): PDF oficial de OGTIC.
  * Decreto 787-26: nota de la Presidencia y reseñas de prensa y de un despacho jurídico.

## Errores detectados y correcciones

1. **Script del curso con error de sintaxis.** `scripts/lab11_impact.py` tenía una cadena con saltos
   de línea literales (`SyntaxError`) y, además, sobrescribía `DECISION_RECORD.md` en cada ejecución.
   Se corrigió para crearlo sólo si no existe.
2. **Dependencia faltante.** Para generar la figura se añadió `matplotlib` a `pyproject.toml` y
   `uv.lock`.
3. **Lectura engañosa de las puertas.** La logística «cumple» sobre la estimación puntual, pero el IC
   95 % de las brechas llega a 0.32 y 0.40. Se añadió la puerta conservadora con el límite superior y
   se reporta que, con estos datos, ningún candidato la cumple.
4. **Hipótesis del proxy territorial.** Se esperaba que quitar `zone` mejorara la equidad. Mejoró la
   brecha de recall, pero triplicó la de FPR (0.327). Se documentó como compromiso, no como solución.
5. **Limitación de fuentes.** El texto oficial del Decreto 787-26 no pudo descargarse del portal de
   la Presidencia (error del sitio). Su descripción se apoya en fuentes secundarias concordantes y
   **debe verificarse contra el texto oficial** antes de citarlo en un trabajo final.

*La clasificación normativa es académica y no constituye asesoría legal.*
