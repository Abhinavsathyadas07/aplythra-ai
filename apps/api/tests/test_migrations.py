from alembic.config import Config
from sqlalchemy import create_engine, inspect

from alembic import command
from tests.conftest import OWNER_URL, reset_and_migrate


def test_upgrade_downgrade_roundtrip() -> None:
    reset_and_migrate("head")
    engine = create_engine(OWNER_URL)
    assert {"users", "audit_logs"} <= set(inspect(engine).get_table_names())

    command.downgrade(Config("alembic.ini"), "base")
    assert not {"users", "audit_logs"} & set(inspect(engine).get_table_names())

    command.upgrade(Config("alembic.ini"), "head")
    assert {"users", "audit_logs"} <= set(inspect(engine).get_table_names())
    engine.dispose()
