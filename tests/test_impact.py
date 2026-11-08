import pandas as pd, pytest
from inf8239_u04.impact import score_risks
def test_complete_risk_is_scored():
    df=pd.DataFrame([{"id":"R1","scenario":"harm","affected":"person","likelihood_1_4":2,"impact_1_4":4,"control":"review","owner":"role","evidence":"log","residual":"medium"}])
    assert score_risks(df).iloc[0].priority==8
def test_placeholder_is_rejected():
    df=pd.DataFrame([{"id":"R1","scenario":"REPLACE","affected":"person","likelihood_1_4":2,"impact_1_4":4,"control":"review","owner":"role","evidence":"log","residual":"medium"}])
    with pytest.raises(ValueError): score_risks(df)
