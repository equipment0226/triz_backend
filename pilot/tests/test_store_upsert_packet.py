"""MySQL conflict updates must not transmit large JSON values twice."""
import json
from types import SimpleNamespace
from sqlalchemy import select
from sqlalchemy.dialects import mysql
from triz import store


def test_mysql_large_state_has_one_payload_binding_and_preserves_update_columns(monkeypatch):
    statements = []
    monkeypatch.setattr(store, 'engine', SimpleNamespace(dialect=mysql.dialect()))
    payload = json.dumps({'history': ['한글 "quote" \\ path'] * 1000}, ensure_ascii=False)
    store._upsert(SimpleNamespace(execute=statements.append), store.states,
                  {'run_id':'test','state_json':payload,'updated_at':'now'})
    compiled = statements[0].compile(dialect=mysql.dialect())
    assert list(compiled.params.values()).count(payload) == 1
    assert set(compiled.params) == {'run_id','state_json','updated_at'}
    sql = str(compiled)
    update = sql.split('ON DUPLICATE KEY UPDATE',1)[1]
    assert 'state_json = VALUES(state_json)' in update
    assert 'updated_at = VALUES(updated_at)' in update
    assert 'run_id =' not in update


def test_sqlite_insert_update_and_partial_update_preserve_other_columns(state):
    with store.engine.begin() as c:
        values = {'run_id':state.run_id,'state_json':'{"sentinel":"before"}','updated_at':'before'}
        store._upsert(c, store.states, values)
        store._upsert(c, store.states, {'run_id':state.run_id,'state_json':'{"sentinel":"after"}'})
        row = c.execute(select(store.states).where(store.states.c.run_id==state.run_id)).mappings().one()
        assert row['state_json'] == '{"sentinel":"after"}'
        assert row['updated_at'] == 'before'
        c.rollback()  # Keep deliberately incomplete JSON out of other run scans.


def test_full_state_roundtrip_keeps_history_and_cost(state):
    from triz.schema import StepRecord
    state.steps.append(StepRecord(node='s6_concept', input_slice={'user':'한글 "quotes" \\'},
        output_json={'concepts':[{'title':'unchanged'}]}, status='OK'))
    state.cost.total_usd = 2.55
    state.scratch['keep_unknown'] = {'all':[1,2,3]}
    store.save_state(state)
    before = state.model_dump(mode='json')
    assert store.load_state(state.run_id).model_dump(mode='json') == before
    store.save_state(state)
    assert store.load_state(state.run_id).model_dump(mode='json') == before
