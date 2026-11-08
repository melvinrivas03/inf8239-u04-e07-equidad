import json
from pathlib import Path
import pandas as pd, yaml
from inf8239_u04.impact import validate_impact, score_risks
out=Path("reports/lab11"); out.mkdir(parents=True,exist_ok=True)
impact=yaml.safe_load(Path("student_inputs/lab11_impact.yml").read_text(encoding="utf-8")); validate_impact(impact)
stake=pd.read_csv("student_inputs/stakeholders.csv")
if stake.astype(str).apply(lambda s:s.str.contains("REPLACE")).any().any(): raise ValueError("Complete stakeholders.csv")
risks=score_risks(pd.read_csv("student_inputs/risk_register.csv")); risks.to_csv(out/"risk_register_scored.csv",index=False); stake.to_csv(out/"stakeholders.csv",index=False)
(out/"rmf_summary.json").write_text(json.dumps({"GOVERN":"owner and policy","MAP":f"{len(risks)} documented risks","MEASURE":"LAB12 completado: ver reports/e07/rmf_summary.json","MANAGE":"withdrawal and appeal documented"},indent=2),encoding="utf-8")
# Corrección U04.E07: el original tenía una cadena con saltos de línea literales (SyntaxError) y además
# sobrescribía el registro de decisión del estudiante en cada ejecución. Sólo se crea si no existe.
record = out / "DECISION_RECORD.md"
if not record.exists():
    record.write_text("# Decision record\n\nREPLACE with evidence, uncertainty, owner and GO/REVIEW/STOP.\n", encoding="utf-8")
print(risks[["id","priority","owner"]].head(3).to_string(index=False))
