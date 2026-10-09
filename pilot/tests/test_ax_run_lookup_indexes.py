"""Existing journal migrations retain usage and make scoped reads indexed."""
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.dialects import mysql

from triz import pipeline, store
from triz.ax import WORKFLOW, effect_history, ledger
from triz.ax.cost_restatements import EVENT, VERSION


def test_existing_journal_keeps_rows_usage_and_uses_indexes(tmp_path, monkeypatch):
    engine = create_engine('sqlite:///' + (tmp_path / 'old-journal.db').as_posix())
    monkeypatch.setattr(store, 'engine', engine)
    monkeypatch.setattr(store, '_initialized', False)
    try:
        store.metadata.create_all(engine)
        ledger.init()
        state = pipeline.create_run('Existing journal migration fixture', workflow_version=WORKFLOW)
        paid = ledger.acquire(state.run_id, 0, {'fixture': 'paid'}, 100)
        ledger.settle(paid, {'keep_provider_receipt': True}, 25)
        unknown = ledger.acquire(state.run_id, 0, {'fixture': 'unknown'}, 200)
        ledger.settle(unknown, {'keep_unknown_receipt': True}, None, status='UNKNOWN')
        with engine.begin() as connection:
            ledger._event(connection, state.run_id, EVENT, {
                'version': VERSION, 'task_adjustments': [
                    {'task_id': paid['task_id'], 'after_microusd': 30}]})
            connection.execute(effect_history.applications.insert().values(
                application_id='existing-application', run_id=state.run_id,
                tenant_id=state.user_id, project_id=state.user_id,
                payload='{"preserve":"all historical fields"}', created_at='2026-10-09'))
            # Reproduce an existing pre-migration schema with its real records.
            for _, name, _ in ledger.RUN_LOOKUP_INDEXES:
                connection.exec_driver_sql('DROP INDEX ' + name)
        tables = (store.runs, store.states, ledger.heads, ledger.artifacts,
                  ledger.snapshots, ledger.tasks, ledger.attempts, ledger.events,
                  ledger.outbox, effect_history.applications)
        def rows():
            with engine.connect() as connection:
                return {table.name: list(connection.execute(select(table).order_by(
                    *table.primary_key.columns)).mappings()) for table in tables}
        queries = (
            ('ix_ax_attempt_run', 'SELECT details FROM ax_task_attempts WHERE run_id = ?'),
            ('ix_ax_event_run_type_time', "SELECT payload FROM ax_events WHERE run_id = ? "
             "AND event_type = 'COST_RESTATEMENT_APPLIED' ORDER BY created_at, event_id"),
            ('ix_ax_effect_application_run', 'SELECT payload FROM ax_effect_applications WHERE run_id = ?'),
        )
        before_rows, before_budget = rows(), ledger.budget(state.run_id)
        assert before_budget['spent_microusd'] == 30 and before_budget['reserved_microusd'] == 200
        with engine.connect() as connection:
            for _, query in queries:
                plan = connection.exec_driver_sql('EXPLAIN QUERY PLAN ' + query, (state.run_id,)).all()
                assert any('SCAN' in row[3] for row in plan)
        # Exercise the actual startup path twice, including existing tables.
        ledger.init()
        ledger.init()
        assert rows() == before_rows
        assert ledger.budget(state.run_id) == before_budget
        with engine.connect() as connection:
            for name, query in queries:
                plan = connection.exec_driver_sql('EXPLAIN QUERY PLAN ' + query, (state.run_id,)).all()
                assert any('SEARCH' in row[3] and name in row[3] for row in plan)
                assert all('USE TEMP B-TREE' not in row[3] for row in plan)
        for table_name, index_name, columns in ledger.RUN_LOOKUP_INDEXES:
            indexes = inspect(engine).get_indexes(table_name)
            assert sum(item['name'] == index_name and tuple(item['column_names']) == columns
                       for item in indexes) == 1
    finally:
        engine.dispose()


@pytest.mark.parametrize('online_failure', [False, True])
def test_mysql_existing_indexes_require_online_ddl_and_restore_session(monkeypatch, online_failure):
    statements, existing = [], {}
    class Connection:
        dialect = mysql.dialect()
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def exec_driver_sql(self, sql):
            statements.append(sql)
            if sql.startswith('ALTER TABLE'):
                if online_failure:
                    raise RuntimeError('Online DDL unavailable')
                table, name, columns = next(spec for spec in ledger.RUN_LOOKUP_INDEXES if spec[1] in sql)
                existing[table] = [{'name': name, 'column_names': list(columns)}]
            return SimpleNamespace(scalar_one=lambda: 37)
        def commit(self):
            pass
    connection = Connection()
    monkeypatch.setattr(ledger, 'inspect', lambda _: SimpleNamespace(
        get_indexes=lambda table: existing.get(table, [])))
    engine = SimpleNamespace(connect=lambda: connection)
    if online_failure:
        with pytest.raises(RuntimeError, match='Online DDL unavailable'):
            ledger.ensure_run_lookup_indexes(engine)
    else:
        ledger.ensure_run_lookup_indexes(engine)
        ledger.ensure_run_lookup_indexes(engine)
    ddl = [sql for sql in statements if sql.startswith('ALTER TABLE')]
    assert len(ddl) == (1 if online_failure else 3)
    assert all(sql.endswith('ALGORITHM=INPLACE, LOCK=NONE') for sql in ddl)
    assert 'SET SESSION lock_wait_timeout = 5' in statements
    assert statements[-1] == 'SET SESSION lock_wait_timeout = 37'
