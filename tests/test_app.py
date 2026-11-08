from pathlib import Path
from streamlit.testing.v1 import AppTest
def test_app_starts_and_discloses_synthetic_case():
    at=AppTest.from_file(Path(__file__).parents[1]/"app.py",default_timeout=20).run(); assert not at.exception; assert any("sintético" in x.value.lower() for x in at.warning)
