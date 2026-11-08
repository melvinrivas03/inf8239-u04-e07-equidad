from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.fairness import audit,gap
from inf8239_u04.model import build_model
def test_fairness_metrics_are_bounded():
    tr,te=temporal_split(load_data()); m=build_model().fit(features(tr),tr.target); _,g,_=audit(te.target,m.predict(features(te)),te.protected_group)
    assert 0<=gap(g,"recall")<=1; assert set(g.index)=={"G1","G2"}
