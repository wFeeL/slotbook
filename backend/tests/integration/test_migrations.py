import pytest
from sqlalchemy import inspect


@pytest.mark.asyncio
async def test_users_and_businesses_tables_exist(db_engine) -> None:  # type: ignore[no-untyped-def]
    async with db_engine.connect() as conn:
        tables = await conn.run_sync(lambda sync_conn: inspect(sync_conn).get_table_names())
    assert "users" in tables
    assert "businesses" in tables
