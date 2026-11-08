from inf8239_u04.data import load_data,features,temporal_split
from inf8239_u04.model import build_model
def test_predictions_are_binary():
    tr,te=temporal_split(load_data()); p=build_model().fit(features(tr),tr.target).predict(features(te)); assert set(p)<={0,1}
