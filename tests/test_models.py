import pytest
from app.models import Base, Click

def test_expected_tables_exist():
    assert set(Base.metadata.tables) == {"users","links", "clicks"}

def test_links_code_is_unique():
    code = Base.metadata.tables["links"].c.code
    assert code.unique

def test_clicks_primary_key_includes_ts():
    pk_columns = {col.name for col in Click.__table__.primary_key.columns}
    assert pk_columns == {"id", "ts"}   