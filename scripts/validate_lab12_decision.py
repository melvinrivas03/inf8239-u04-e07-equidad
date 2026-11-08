from pathlib import Path
import yaml
d=yaml.safe_load(Path("student_inputs/lab12_decision.yml").read_text(encoding="utf-8")); missing=[k for k,v in d.items() if str(v).strip() in {"","REPLACE"}]
if missing: raise ValueError(f"Complete: {missing}")
print("decision_status: documented")
