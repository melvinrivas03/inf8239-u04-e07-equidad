from inf8239_u04.data import load_data, temporal_split
df=load_data(); train,test=temporal_split(df)
print("shape",df.shape); print("target",df.target.value_counts(normalize=True).round(3).to_dict()); print("groups",df.protected_group.value_counts().to_dict()); print("train_end",train.received_date.max()); print("test_start",test.received_date.min()); print("excluded_from_model",["case_id","received_date","protected_group","target"])
