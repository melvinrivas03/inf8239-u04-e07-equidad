import pytest
from inf8239_u04.data import load_data,validate_schema
def test_prohibited_name_rejected():
    with pytest.raises(ValueError): validate_schema(load_data().assign(name="A"))
