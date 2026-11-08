import argparse, json
from pathlib import Path
from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.fairness import audit,intersectional
from inf8239_u04.model import build_model,fit_measure
p=argparse.ArgumentParser(); p.add_argument("--model",choices=["logistic","tree"],default="logistic"); args=p.parse_args()
out=Path("reports/lab12")/args.model; out.mkdir(parents=True,exist_ok=True)
df=load_data(); train,test=temporal_split(df); model=build_model(args.model); resources=fit_measure(model,features(train),train.target,f"models/{args.model}.joblib"); pred=model.predict(features(test))
overall,groups,diff=audit(test.target,pred,test.protected_group); _,inter,_=audit(test.target,pred,intersectional(test))
groups.to_csv(out/"fairness_by_group.csv"); inter.to_csv(out/"fairness_intersectional.csv")
(out/"global_metrics.json").write_text(json.dumps({"metrics":{k:float(v) for k,v in overall.items()},"differences":{k:float(v) for k,v in diff.items()},"resources":resources},indent=2),encoding="utf-8")
print(groups.round(3)); print(resources)
