
import pytest
from chatmaild.database import Database


@pytest.fixture()
def db(tmpdir):
    db_path = tmpdir / "passdb.sqlite"
    print("database path:", db_path)
    return Database(db_path)

