"""Raw read-only ports: importing legacy metadata never invokes its init/load/save."""
import hashlib
import json
import time
from sqlalchemy import select, inspect
from .domain import PatentError, digest


class LegacyReader:
    def __init__(self, engine=None):
        from triz import store
        self.store = store
        from .sql_guard import guarded
        self.engine = guarded(engine or store.engine)

    def principal(self, token):
        if not token or len(token) > 128:
            return None
        s = self.store
        with self.engine.connect() as c:
            row = c.execute(select(s.sessions.c.user_id).where(
                s.sessions.c.token_hash == hashlib.sha256(token.encode()).hexdigest(),
                s.sessions.c.expires_at > time.time())).first()
        return row[0] if row else None

    def is_patent_tester(self, owner):
        from .access import TESTER_EMAIL
        with self.engine.connect() as c:
            email=c.execute(select(self.store.accounts.c.email).where(
                self.store.accounts.c.user_id==owner)).scalar()
        return isinstance(email,str) and email.strip().casefold()==TESTER_EMAIL

    def raw(self, owner, run_id):
        s = self.store
        with self.engine.connect() as c:
            row = c.execute(select(s.states.c.state_json).join(s.runs, s.states.c.run_id == s.runs.c.run_id)
                            .where(s.runs.c.run_id == run_id, s.runs.c.user_id == owner)).first()
        if not row:
            raise PatentError('NOT_FOUND', '내 해결안을 찾을 수 없습니다.', 404)
        return json.loads(row[0])

    @staticmethod
    def concepts(state):
        value = state.get('concepts', [])
        # Verified GlobalState uses concepts; unsupported shapes fail closed.
        return value if isinstance(value, list) else []

    def preview(self, owner, run_id, concept_id):
        state = self.raw(owner, run_id)
        concept = next((x for x in self.concepts(state) if x.get('id') == concept_id), None)
        if concept is None:
            raise PatentError('NOT_FOUND', '해결안을 찾을 수 없습니다.', 404)
        ids = set(concept.get('evidence_ids', []))
        evidence = [x for x in state.get('evidence', []) if x.get('id') in ids]
        with self.engine.connect() as c:
            published = c.execute(select(self.store.published_runs).where(self.store.published_runs.c.run_id == run_id)).mappings().first()
        payload = {'source_run_id': run_id, 'concept_id': concept_id, 'concept': concept,
                   'problem': state.get('intake', {}).get('frame', {'raw_query': state.get('raw_query', '')}), 'references': evidence,
                   'raw_publication': {'origin': 'TRIZ_STUDIO_BETA', 'published_run': dict(published) if published else None},
                   'scope_note': '베타 자료는 이번 외부 공개이력 분석에서 제외합니다. 법적 공개 여부는 판단하지 않습니다.'}
        return {**payload, 'source_hash': digest(payload), 'legacy_state_hash': digest(state)}

    def schema_fingerprint(self):
        inspector = inspect(self.engine)
        names = sorted(set(inspector.get_table_names()) & set(self.store.metadata.tables))
        structure = {name: {'columns':[{k: str(v) if k == 'type' else v for k, v in col.items()}
                            for col in inspector.get_columns(name)],
                           'primary_key':inspector.get_pk_constraint(name),
                           'indexes':inspector.get_indexes(name),
                           'unique':inspector.get_unique_constraints(name),
                           'foreign_keys':inspector.get_foreign_keys(name)} for name in names}
        return digest(structure)

    def list(self, owner, offset=0, limit=20):
        s = self.store
        with self.engine.connect() as c:
            rows = c.execute(select(s.runs.c.run_id, s.runs.c.title, s.states.c.state_json)
                .join(s.states, s.states.c.run_id == s.runs.c.run_id).where(s.runs.c.user_id == owner)
                .order_by(s.runs.c.started_at.desc(), s.runs.c.run_id).offset(offset).limit(limit + 1)).all()
        return {'items': [{'run_id': r.run_id, 'title': r.title, 'concepts': [
            {'id': x.get('id'), 'title': x.get('title')} for x in self.concepts(json.loads(r.state_json))]}
            for r in rows[:limit]], 'next_offset': offset + limit if len(rows) > limit else None}
