# Registro de decisión · Territorial Review DSS (sintético)

**Responsable de la decisión:** Melvin H. Rivas Genao (matrícula 100279298), como analista del
expediente U04.E07.
**Propietario institucional (RACI):** Institutional Owner, que firma y activa la condición de retiro.
**Fecha:** 8 de noviembre de 2026.
**Revisión siguiente:** al cerrar la primera ventana mensual del piloto, o antes si se cumple una
condición de retiro.

## Decisión: **LIMITAR**

Se autoriza un **piloto acotado** con la regresión logística del curso, usada **sólo como orden
sugerido de revisión humana**:

1. Todos los casos siguen en la cola. El sistema nunca cierra, descarta ni decide un caso.
2. El grupo protegido no se usa al decidir. ThresholdOptimizer queda excluido.
3. Se informa a las personas del uso del sistema y se habilita la apelación ante un revisor distinto
   (5 días hábiles).
4. La brecha de recall y la de FPR se monitorean cada mes, con IC 95 % por bootstrap, y se reporta el
   soporte de cada intersección.
5. Cada mes se revisa al azar un 5 % de los casos de baja prioridad, para medir los falsos negativos
   que el orden oculta.

## Evidencia (reports/e07/)

| Elemento | Valor | Lectura |
|---|---|---|
| Recall global (puerta ≥ 0.68) | 0.717 | Cumple |
| Recall G1 / G2 | 0.653 / 0.791 | G1 se detecta menos: es el daño prioritario (falso negativo) |
| Brecha de recall (≤ 0.16) | 0.138, IC 95 % [0.010, 0.318] | Cumple en la estimación puntual; **no se puede confirmar** con 59 casos de G2 |
| Brecha de FPR (≤ 0.16) | 0.125, IC 95 % [0.006, 0.398] | Igual que la anterior |
| Intersecciones sin soporte | 4 de 8 | No se interpretan como brechas; se reportan y se piden más datos |
| Costo | 3.6 KB, < 0.1 ms por caso | Suficiente; el árbol ocupa el doble y falla las puertas (Green AI) |

## Alternativas consideradas

| Alternativa | Por qué no se adopta (o queda en reserva) |
|---|---|
| Regla transparente (≥ 3 incidentes previos) | Mayor recall (0.84), pero marca el 71 % de los casos con FPR de 0.52 a 0.63, y no ordena: satura la revisión. **Es el fallback si se activa el retiro.** |
| Umbral 0.56 calibrado en validación | Menor brecha de FPR (0.077), pero el recall baja a 0.696, muy cerca de la puerta. Va en contra del daño priorizado. Queda como variante si el escrutinio innecesario pasa a ser el daño principal. |
| Sin la variable `zone` | La brecha de recall baja a 0.114, pero la de FPR sube a 0.327. Quitar un posible proxy no garantiza equidad. |
| ExponentiatedGradient | Brecha de recall de 0.079, pero brecha de FPR de 0.212, decisiones aleatorizadas difíciles de explicar o apelar, y 135 KB. |
| ThresholdOptimizer | Usa el grupo protegido al decidir: trato desigual (Constitución, art. 39). Excluido. |

## Incertidumbre y límites

* Prueba con 160 casos (101 en G1 y 59 en G2) y datos **sintéticos**: la validez externa es nula sin
  una nueva evaluación.
* Las tasas base son distintas (0.64 en G2 y 0.50 en G1), así que no pueden igualarse a la vez todas
  las tasas de error.
* Una brecha observada **justifica investigar, no prueba discriminación causal**. Puede venir de las
  tasas base, del tamaño de muestra o de variables correlacionadas.
* La brecha es una diferencia absoluta: su IC percentil no incluye 0 por construcción. Por eso la
  decisión se basa en el **límite superior**.

## Condición de retiro (volver a la regla transparente)

Se retira el sistema si ocurre cualquiera de estas condiciones:
* el recall global queda por debajo de 0.68, o la brecha de recall por encima de 0.16, en dos
  ventanas mensuales consecutivas con al menos 100 casos cada una;
* con al menos 200 casos por grupo, el límite superior del IC 95 % de la brecha de recall sigue por
  encima de 0.16;
* se detecta un uso fuera de alcance;
* la apelación no responde en plazo.

## Condición para ampliar (pasar de LIMITAR a DESPLEGAR)

Se amplía el uso si se cumplen todas estas condiciones:
* hay al menos 200 casos por grupo con el límite superior del IC de ambas brechas en 0.16 o menos;
* se ha consultado a representantes de las personas afectadas;
* si lo opera una entidad pública, se ha hecho la evaluación de impacto ético y de derechos y el
  registro que exige el Decreto 787-26.
