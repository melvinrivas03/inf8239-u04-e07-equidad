import pandas as pd, pytest
from inf8239_u04.data import load_data,validate_schema
def test_dataset_contract():
    df=load_data(); assert len(df)>=500; assert df.case_id.is_unique
def test_direct_identifier_rejected():
    df=load_data().assign(email="x@example.org")
    with pytest.raises(ValueError,match="Direct identifiers"): validate_schema(df)
