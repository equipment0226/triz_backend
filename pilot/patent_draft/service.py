"""The single patent governor/reducer used by HTTP, MCP and durable workers."""
from __future__ import annotations

import hashlib
import json
import os
from sqlalchemy import insert, select, update, inspect
from pydantic import ValidationError
from .domain import (Bootstrap, Mutation, Invention, ClaimTree, DocumentAST, DrawingSpec, Questions,
    SearchPlan, ClaimChart, Economics, Reconciliation, Review, PatchProposal, TaskTicket,
    PatentError, canonical, digest, ident, PROFILE, SCOPE, ROLES, Facts)
from .repository import Repository, cases, tasks, assets, now
from .legacy import LegacyReader
from .models import ModelProfile, Gateway, reserve, settle, balance
from .sources import SourceService
from .learning import LegacyLearningAdapter, feedback_event
from . import forms, rules
from .intake import (APPLICATION_QUESTIONS, complete as intake_complete, context_from_answers,
                     questions as intake_questions, unanswered)

OPERATIONS = {
    'patent_extract_invention': ('T1', 'invention', Invention),
    'patent_plan_questions': ('T1', 'questions', Questions),
    'patent_plan_search': ('T2', 'search_plan', SearchPlan),
    'patent_search_local': ('CODE', 'sources', None),
    'patent_enrich_sources': ('CODE', 'source_detail', None),
    'patent_build_claim_chart': ('T2', 'claim_chart', ClaimChart),
    'patent_assess_economics': ('T2', 'economics', Economics),
    'patent_draft_claims': ('T2', 'claims', ClaimTree),
    'patent_draft_specification': ('T2', 'specification', DocumentAST),
    'patent_build_drawings': ('T2', 'drawings', DrawingSpec),
    'patent_check_rules': ('CODE', 'checks', None),
    'patent_review_content': ('T3', 'review', Review),
    'patent_reconcile_issues': ('T2', 'reconciliation', Reconciliation),
    'patent_apply_patch': ('CODE', 'patch', None),
    'patent_final_review': ('T3', 'review', Review),
    'patent_render_package': ('CODE', 'export', None),
    'patent_emit_feedback': ('CODE', 'feedback', None),
}
MATERIAL_TYPES = {'source', 'invention', 'facts', 'questions', 'review_questions', 'answers', 'search_plan', 'sources', 'sample_image', 'application_questions', 'application_context','attachments',
                  'source_detail', 'claim_chart', 'economics', 'claims', 'specification', 'drawings'}
SCHEMAS = {'invention': Invention, 'claims': ClaimTree, 'specification': DocumentAST, 'drawings': DrawingSpec,'facts':Facts}
INSTRUCTIONS = {
    'invention': 'Treat the selected solution as a starting proposal. Apply the owner application_context changes and constraints; preserve risks and unknowns. Extract only supported technical features. User answers are not measurements. New facts are DERIVED_PROPOSAL; effects are HYPOTHESIS unless an actual measurement source is supplied.',
    'questions': 'Ask unresolved application changes, constraints, risks and missing technical, ownership and external disclosure facts. Read application_context and existing answers before asking follow-ups. Do not repeat answered questions. Unresolved risks remain unknown and must not become confirmed facts. Never ask about excluded TRIZ_STUDIO_BETA disclosure. Include unique stable question IDs (never APPLICATION_ prefix), why, affected fields and blocking status.',
    'search_plan': 'Use at most four mechanism/synonym/classification queries across industries. Record corpus/fulltext and historical/nonpatent coverage gaps.',
    'claim_chart': 'Compare individual technical features to individual documents and exact passages. Abstract-only evidence must remain UNKNOWN for full claim disclosure.',
    'economics': 'Advisory only. No invented monetary valuations or probabilities. Mark uncertainty.',
    'claims': 'Use an independent claim and supported dependent claims, with feature IDs and description support. Never invent technical facts. A draft scope requires separate owner approval.',
    'specification': 'Use section IDs title,technical_field,background,problem,solution,effects,drawing_description,embodiments. Include abstract and available applicant/inventor facts. Never fabricate personal identifiers. Clearly separate prior art and proposals.',
    'drawings': 'Produce a DrawingSpec. Nodes require id,label,feature_id; edges from,to,label. All features must exist. Provide one sample_prompt_en for black-and-white line art of existing geometry only. These are concept drawings pending technical/visual review. Do not claim official form validation.',
    'reconciliation': 'Propose issue-specific typed patches or questions. You cannot remove rules, overrule reviews, grant approvals or declare readiness. Preserve unresolved issue IDs.',
}


class Service:
    def __init__(self, repository, legacy=None, profile=None, gateway=None, sources=None):
        self.repo = repository
        self.legacy = legacy or LegacyReader()
        self.profile = profile or ModelProfile()
        self.gateway = gateway or Gateway()
        self.sources = sources or SourceService(repository)

    def capabilities(self):
        return {'enabled': os.getenv('PATENT_ENABLED', 'false').lower() == 'true',
                'dispatch_enabled': os.getenv('PATENT_DISPATCH_ENABLED', 'false').lower() == 'true',
                'model_profile': PROFILE, 'configured_tiers': sorted(self.profile.models),
                'providers': sorted({m.base_url for m in self.profile.models.values()}),
                'required_review_micro_usd': self.profile.review_plan() if 'T3' in self.profile.models else None,
                't3_reasoning_configured': bool(self.profile.models.get('T3') and self.profile.models['T3'].reasoning),
                'kipris_configured': bool(os.getenv('KIPRIS_API_KEY')), 'kipris_live_validation': 'NOT_RUN',
                'drawing_provider': 'STABLE_DIFFUSION_CPU', 'drawing_configured': bool(os.getenv('PATENT_DRAWING_URL')),
                'learning': LegacyLearningAdapter().capabilities(), 'editor_validation': 'NOT_RUN',
                'formats': ['DOCX','HTML','MARKDOWN','JSON','SVG','ZIP'], 'automatic_filing': False}

    def open(self, owner, body, key):
        from .access import require_tester
        require_tester(self.legacy,owner)
        body = Bootstrap.model_validate(body).model_dump()
        request_key = self.repo.request_key(owner, 'bootstrap', key)
        with self.repo.engine.connect() as c:
            previous = self.repo.replay(c, request_key, body)
        if previous is not None:
            return previous
        source = self.legacy.preview(owner, body['source_run_id'], body['concept_id'])
        if source['source_hash'] != body['expected_source_hash']:
            raise PatentError('SOURCE_VERSION_CONFLICT', '해결안이 변경됐습니다. 미리보기를 다시 확인해 주세요.')
        case_id = ident('pat')
        case = {'case_id': case_id, 'owner_id': owner, 'visibility': 'PRIVATE', 'revision': 0, 'epoch': 1,
            'title': source['concept'].get('title') or '특허 초안', 'purpose': body['purpose'],
            'source_run_id': body['source_run_id'], 'concept_id': body['concept_id'], 'source_hash': source['source_hash'],
            'profile': body['profile'], 'jurisdiction': 'KR', 'rulepack_version': rules.PACK['version'],
            'model_profile': PROFILE, 'model_config': {}, 'policy_version': 'patent-safe-v1', 'initial_policy_version': 'patent-safe-v1',
            'scope_policy_version': SCOPE, 'form_version': forms.FORM_VERSION,
            'form_registry_hash': __import__('patent_draft.form_registry',fromlist=['fingerprint']).fingerprint(),
            'legacy_adapter': 'READ_ONLY_NO_GATE_EQUIVALENCE', 'learning_status': 'TELEMETRY_ONLY',
            'execution_status': 'CREATED', 'document_status': 'INCOMPLETE', 'evidence_status': 'NOT_RUN',
            'editor_validation': 'NOT_RUN', 'filing_status': 'NOT_FILED', 'artifacts': {}, 'snapshot_id': '',
            'repair_rounds': 0, 'provider_authorization': None, 'review_plan_reserved': False,
            'budget': {'cap_micro_usd': 0, 'spent_micro_usd': 0, 'reserved_micro_usd': 0,
                       'review_plan_micro_usd': 0, 'uncertain_micro_usd': 0}, 'last_error': None,
            'legacy_schema_hash': self.legacy.schema_fingerprint()}
        with self.repo.engine.begin() as c:
            self.repo.artifact(c, case, 'source', source, producer='LEGACY_READ_ONLY')
            self.repo.artifact(c, case, 'application_questions', {'questions':APPLICATION_QUESTIONS},
                               [case['artifacts']['source']], producer='MANDATORY_OWNER_INTAKE')
            case['document_status'] = 'INCOMPLETE'
            c.execute(insert(cases).values(case_id=case_id, owner_id=owner, revision=0, epoch=1,
                                          body=canonical(case), updated_ms=now()))
            self.repo.append(c, case_id, 'event', {'type': 'CREATED', 'revision': 0, 'epoch': 1})
            self.repo.remember(c, request_key, body, case)
        return case

    def material(self, owner, case, conn=None, snapshot_id=None):
        snapshot = self.repo.record(owner, case['case_id'], snapshot_id or case['snapshot_id'], conn)
        if snapshot['kind'] != 'snapshot':
            raise PatentError('SNAPSHOT_INVALID', '유효한 스냅샷이 아닙니다.', 422)
        return {kind: self.repo.record(owner, case['case_id'], version, conn)['payload']
                for kind, version in snapshot['members'].items()}

    def approvals(self, owner, case, c=None):
        return {a['approval_type']: a['content_hash']
                for a in self.repo.records(owner, case['case_id'], 'approval', c)
                if a.get('epoch') == case['epoch'] and a.get('bound_versions') == self.approval_versions(case, a['approval_type'])}

    @staticmethod
    def approval_versions(case, approval_type):
        kinds = {'source', 'application_context', 'answers', 'facts', 'invention','attachments'}
        if approval_type == 'G2':
            kinds.add('claims')
        return {k: v for k, v in sorted(case['artifacts'].items()) if k in kinds}

    def invalidate(self, c, case, kinds, reason):
        """Retain the ledger; retire derived heads and unstarted stale tasks only."""
        dependents = {'facts': {'invention','questions','review_questions'},
                      'invention': {'search_plan','sources','claim_chart','economics','claims','specification','drawings'},
                      'search_plan': {'sources','claim_chart'}, 'sources': {'claim_chart'},
                      'claims': {'specification','drawings'}, 'specification': {'drawings'},
                      'drawings': {'sample_image'}}
        affected = set(kinds)
        while True:
            expanded = affected | set().union(*(dependents.get(k, set()) for k in affected))
            if expanded == affected:
                break
            affected = expanded
        retired = {k: case['artifacts'].pop(k) for k in sorted(affected) if k in case['artifacts']}
        if retired:
            self.repo.append(c, case['case_id'], 'invalidation', {'reason': reason, 'retired_versions': retired})
        case['document_status'] = 'DRAFT_WITH_OPEN_ISSUES'
        if case['execution_status'] not in ('CREATED','CANCELLED','PAUSED_USER'):
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'INPUT_UPDATED'
        return retired

    def retire_stale_queued(self, c, case, cancel=False):
        for row in c.execute(select(tasks).where(tasks.c.case_id == case['case_id'], tasks.c.status.in_(['QUEUED','HELD'])).with_for_update()).mappings():
            body = json.loads(row['body'])
            ticket = body['ticket']
            if not cancel and ticket['epoch'] == case['epoch'] and set(ticket['read_version_ids']) == set(self.readset(case, ticket['review_role'])):
                continue
            reserved = body['reserved_micro_usd']
            case['budget']['reserved_micro_usd'] -= reserved
            if ticket['tier'] == 'T3' and not cancel:
                case['budget']['review_plan_micro_usd'] += reserved
            body['result'] = {'reason': 'CANCELLED' if cancel else 'INPUT_CHANGED', 'charged_micro_usd': 0}
            c.execute(update(tasks).where(tasks.c.task_id == row['task_id']).values(
                status='CANCELLED' if cancel else 'STALE', body=canonical(body), lease_until_ms=0))
            self.repo.append(c, case['case_id'], 'cost', {'task_id': row['task_id'],
                'reservation_id': ticket['budget_reservation_id'], 'reserved_micro_usd': reserved,
                'actual_micro_usd': 0, 'status': 'RELEASED_NOT_DISPATCHED', 'tier': ticket['tier']})

    def sample_image(self, owner, case, material, c=None):
        if 'sample_image' not in material:
            return None
        if c is None:
            with self.repo.engine.connect() as conn:
                return self.sample_image(owner, case, material, conn)
        self.repo.get(owner, case['case_id'], c)
        image = c.execute(select(assets.c.content).where(assets.c.case_id == case['case_id'],
            assets.c.asset_id == material['sample_image']['asset_id'], assets.c.mime == 'image/png')).scalar()
        if image is None:
            raise PatentError('IMAGE_ASSET_MISSING', '스냅샷에 연결된 샘플 이미지 파일을 찾을 수 없습니다.')
        return image

    def current_reviews(self, owner, case, c=None):
        versions = set(case['artifacts'].values())
        results = self.repo.records(owner, case['case_id'], 'review', c)
        current = []
        for review in results:
            if review['epoch'] == case['epoch'] and set(review['covered_artifact_ids']) == set(self.readset(case, review['role'])) and review.get('model_profile') == PROFILE:
                current.append(review)
        return current

    def readset(self, case, role=None):
        if role == 'TECHNICAL_CONTENT':
            kinds = {'invention','claims','specification','drawings','sources','source_detail','application_context','facts','answers','attachments'}
        elif role == 'PATENT_CONTENT':
            kinds = {'source','invention','facts','claims','specification','drawings','sources','source_detail','claim_chart','sample_image','application_context','answers','attachments'}
        else:
            kinds = MATERIAL_TYPES
        return [v for k, v in sorted(case['artifacts'].items()) if k in kinds]

    def runtime_checks(self, owner, case, material, c=None):
        if c is None:
            with self.repo.engine.connect() as connection:
                return self.runtime_checks(owner,case,material,connection)
        from .observations import collect
        reviews=self.current_reviews(owner,case,c)
        runtime=collect(self,owner,case,material,c)
        return rules.checks(case, material, reviews, runtime)

    def mutate(self, owner, case_id, operation, body, key):
        from .access import require_tester
        require_tester(self.legacy,owner)
        body = Mutation.model_validate(body).model_dump()
        try:
            return self.repo.mutate(owner, case_id, operation, body, key,
                                    lambda c, case, payload: self.reduce(c, owner, case, operation, payload))
        except ValidationError:
            raise PatentError('PAYLOAD_INVALID', '입력 자료의 형식과 필수 항목을 확인해 주세요.', 422) from None

    def reduce(self, c, owner, case, operation, payload):
        material = self.material(owner, case, c)
        if operation == 'metadata':
            if set(payload) - {'title', 'purpose'} or not all(isinstance(v, str) and 0 < len(v) <= 2000 for v in payload.values()):
                raise PatentError('METADATA_INVALID', '제목과 목적만 수정할 수 있습니다.', 422)
            case.update(payload)
        elif operation == 'budget-authorizations':
            if set(payload) != {'cap_micro_usd','allow_provider_transfer','purpose','retention_acknowledged'}:
                raise PatentError('BUDGET_AUTHORIZATION', '예산·공급자 전송 목적·보관정책 확인이 필요합니다.', 422)
            amount = payload['cap_micro_usd']
            if type(amount) is not int or not 0 < amount <= 100_000_000 or amount < case['budget']['cap_micro_usd']:
                raise PatentError('BUDGET_LIMIT', '명시적 상한은 기존 이상, 최대 US$100까지 지정할 수 있습니다.', 422)
            if payload['allow_provider_transfer'] is not True or payload['retention_acknowledged'] is not True or not payload['purpose']:
                raise PatentError('PROVIDER_CONSENT', '공급자 전송과 보관정책을 확인해야 합니다.', 422)
            self.profile.require()
            snapshot = self.profile.snapshot()
            if case['model_config'] and case['model_config'] != snapshot:
                raise PatentError('MODEL_PROFILE_PINNED', '현재 사건의 모델 구성을 변경할 수 없습니다.')
            case['model_config'] = snapshot
            case['budget']['cap_micro_usd'] = amount
            case['provider_authorization'] = {'purpose': payload['purpose'], 'retention_acknowledged': True,
                                              'providers': sorted({v['base_url'] for v in snapshot.values()})}
            self.repo.append(c, case['case_id'], 'budget_authorization', {'actor': owner, **payload, 'profile': snapshot})
        elif operation == 'withdraw-attachment':
            if set(payload)!={'asset_id','reason'} or not isinstance(payload['reason'],str) or not payload['reason'].strip() or len(payload['reason'])>2000:
                raise PatentError('ATTACHMENT_WITHDRAWAL','첨부자료 ID와 제외 사유를 입력해 주세요.',422)
            if case['execution_status']=='CANCELLED':
                raise PatentError('TERMINAL_CASE','종료된 사건의 자료를 변경할 수 없습니다.')
            documents=material.get('attachments',{}).get('documents',[])
            retained=[d for d in documents if d['asset_id']!=payload['asset_id']]
            if len(retained)==len(documents):
                raise PatentError('NOT_FOUND','현재 검토에 포함된 첨부자료를 찾을 수 없습니다.',404)
            previous=case['artifacts']['attachments']
            self.invalidate(c,case,{'invention','questions','review_questions'},'ATTACHMENT_WITHDRAWN')
            self.repo.artifact(c,case,'attachments',{'documents':retained},[previous],producer='OWNER_WITHDRAWAL')
            self.repo.append(c,case['case_id'],'attachment_withdrawal',payload)
            self.retire_stale_queued(c,case)
        elif operation in ('start', 'resume'):
            if case['execution_status'] in ('CANCELLED','COMPLETED'):
                raise PatentError('TERMINAL_CASE', '종료된 실행은 재개할 수 없습니다.')
            if not intake_complete(material):
                case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'APPLICATION_CONTEXT'
                return {'required_question_ids': [q['id'] for q in APPLICATION_QUESTIONS]}
            if os.getenv('PATENT_DISPATCH_ENABLED', 'false').lower() != 'true':
                raise PatentError('DISPATCH_DISABLED', '특허 작업 실행이 아직 활성화되지 않았습니다.', 503)
            profile = ModelProfile.pinned(case['model_config']).require()
            if not case['provider_authorization']:
                raise PatentError('BUDGET_AUTHORIZATION', '특허 전용 실행 예산을 먼저 승인해야 합니다.')
            if not case['review_plan_reserved']:
                plan = profile.review_plan()
                if balance(case['budget']) < plan:
                    case['execution_status'], case['last_error'] = 'PAUSED_BUDGET', 'REQUIRED_T3_RESERVATION'
                    return {'required_review_micro_usd': plan}
                case['budget']['review_plan_micro_usd'] = plan
                case['review_plan_reserved'] = True
            case['execution_status'], case['last_error'] = 'QUEUED', None
            c.execute(update(tasks).where(tasks.c.case_id == case['case_id'], tasks.c.status == 'HELD').values(status='QUEUED'))
            self.plan(c, owner, case)
        elif operation in ('pause','cancel'):
            case['execution_status'] = 'PAUSED_USER' if operation == 'pause' else 'CANCELLED'
            if operation == 'pause':
                c.execute(update(tasks).where(tasks.c.case_id == case['case_id'], tasks.c.status == 'QUEUED').values(status='HELD'))
            # Epoch fences every in-flight result. Charges still settle.
            if operation == 'cancel':
                case['epoch'] += 1
                self.retire_stale_queued(c, case, cancel=True)
                case['budget']['review_plan_micro_usd'] = 0
        elif operation == 'answers':
            if case['execution_status'] == 'CANCELLED':
                raise PatentError('TERMINAL_CASE', '취소된 실행의 입력은 변경할 수 없습니다.')
            if set(payload) - {'answers','facts'}:
                raise PatentError('ANSWER_INVALID', '답변과 확인 사실만 저장할 수 있습니다.', 422)
            questions = {q['id'] for q in intake_questions(material)}
            answers = payload.get('answers', {})
            if not isinstance(answers, dict) or set(answers) - questions or any(not isinstance(v, str) or len(v) > 8000 for v in answers.values()):
                raise PatentError('ANSWER_INVALID', '질문 ID와 답변을 확인해 주세요.', 422)
            answers = {k: v.strip() for k, v in answers.items()}
            combined = {**material.get('answers', {}), **answers}
            changed = {k for k in answers if answers[k] != material.get('answers', {}).get(k)}
            context = material.get('application_context', {})
            if any(q['id'] in answers for q in APPLICATION_QUESTIONS):
                context = context_from_answers(owner, material.get('application_context', {}), answers)
            context_changed = context != material.get('application_context', {})
            facts = material.get('facts', {})
            if 'facts' in payload:
                if not isinstance(payload['facts'], dict) or len(canonical(payload['facts'])) > 30000:
                    raise PatentError('FACTS_INVALID', '확인 사실의 형식 또는 크기를 확인해 주세요.', 422)
                facts = {**facts, **payload['facts']}
                facts=Facts.model_validate(facts).model_dump(exclude_unset=True)
            facts_changed = facts != material.get('facts', {})
            if context_changed:
                self.invalidate(c, case, {'invention','questions','review_questions'}, 'APPLICATION_CONTEXT_CHANGED')
                # Remove obsolete generated answers, while retaining their ledger history.
                combined = {k: v for k, v in combined.items() if k in {q['id'] for q in APPLICATION_QUESTIONS}}
            elif changed or facts_changed:
                affected = set().union(*(set(q['affected_fields']) for q in intake_questions(material) if q['id'] in changed))
                # A generated question cannot remove owner facts or pinned input.
                if 'facts' in affected:
                    affected = (affected - {'facts'}) | {'invention'}
                self.invalidate(c, case, {'invention'} if facts_changed else affected, 'OWNER_INPUT_CHANGED')
            if context_changed:
                self.repo.artifact(c, case, 'application_context', context, [case['artifacts']['application_questions']], producer='OWNER_INPUT')
            if combined != material.get('answers', {}):
                self.repo.artifact(c, case, 'answers', combined, parents=[v for k, v in case['artifacts'].items()
                    if k in ('application_questions','questions','review_questions')], producer='OWNER_INPUT')
            if facts_changed:
                self.repo.artifact(c, case, 'facts', facts)
            self.retire_stale_queued(c, case)
        elif operation == 'approvals':
            if not intake_complete(material):
                raise PatentError('APPLICATION_CONTEXT_REQUIRED', '적용 변경사항·제약조건·위험요소를 먼저 직접 입력해 주세요.')
            if unanswered(material):
                raise PatentError('QUESTIONS_REQUIRED', '추가 확인이 필요한 질문에 먼저 답변해 주세요.')
            approval_type = payload.get('approval_type')
            target = 'invention' if approval_type == 'G1' else 'claims' if approval_type == 'G2' else None
            if target is None or target not in material or payload.get('content_hash') != digest(material[target]):
                raise PatentError('APPROVAL_SCOPE', '현재 발명정보 또는 청구범위의 정확한 내용을 확인해야 합니다.')
            self.repo.append(c, case['case_id'], 'approval', {'actor': owner, 'approval_type': approval_type,
                'content_hash': payload['content_hash'], 'snapshot_id': case['snapshot_id'], 'epoch': case['epoch'],
                'bound_versions': self.approval_versions(case, approval_type)})
        elif operation == 'patches':
            patch = PatchProposal.model_validate(payload).model_dump()
            if patch['target_type'] not in material or digest(material[patch['target_type']]) != patch['before_hash']:
                raise PatentError('PATCH_CONFLICT', '수정 대상이 변경됐습니다.')
            return {'patch_id': self.repo.append(c, case['case_id'], 'patch_proposal', patch)}
        elif operation == 'apply-patch':
            proposal = self.repo.record(owner, case['case_id'], payload.get('patch_id'), c)
            if proposal['kind'] != 'patch_proposal':
                raise PatentError('PATCH_INVALID', '수정 제안이 아닙니다.', 422)
            patch = PatchProposal.model_validate({k: proposal[k] for k in PatchProposal.model_fields})
            before = material.get(patch.target_type)
            if before is None or digest(before) != patch.before_hash:
                raise PatentError('PATCH_CONFLICT', '수정 대상이 변경됐습니다.')
            replacement = SCHEMAS[patch.target_type].model_validate(patch.replacement).model_dump() if patch.target_type in SCHEMAS else patch.replacement
            if patch.target_type == 'invention':
                for feature in replacement['features']:
                    feature['provenance'] = 'DERIVED_PROPOSAL'
                for effect in replacement.get('effects', []):
                    effect['evidence_status'] = 'HYPOTHESIS'
            previous_version = case['artifacts'][patch.target_type]
            self.invalidate(c, case, {patch.target_type}, 'OWNER_APPROVED_PATCH')
            version = self.repo.artifact(c, case, patch.target_type, replacement,
                parents=[previous_version], producer='OWNER_APPROVED_PATCH')
            self.repo.append(c, case['case_id'], 'patch_applied', {'patch_id':proposal['id'],
                'actor':owner,'before_version_id':previous_version,'after_version_id':version,
                'before_hash':patch.before_hash,'epoch':case['epoch']})
            self.retire_stale_queued(c, case)
            case['document_status'] = 'DRAFT_WITH_OPEN_ISSUES'
            return {'artifact_version_id': version}
        elif operation == 'enrichment-requests':
            if set(payload) != {'application_number','issue_id','missing_fields','authorized_api_calls'} or payload['authorized_api_calls'] != 1:
                raise PatentError('ENRICHMENT_SCOPE', '누락 자료에 대한 단일 상세 조회를 명시해야 합니다.', 422)
            return self.issue(c, case, 'patent_enrich_sources', payload=payload)
        elif operation == 'sample-image':
            if payload:
                raise PatentError('DRAWING_PAYLOAD', '기존 기술 구성으로만 이미지를 생성할 수 있습니다.', 422)
            from .image_jobs import queue
            return queue(self, c, case, material)
        elif operation == 'feedback':
            event = feedback_event(case, payload)
            for prior in self.repo.records(owner, case['case_id'], 'feedback', c):
                if prior['dedupe_key'] == event['dedupe_key']:
                    return {'feedback_id': prior['id'], 'learning_status': 'TELEMETRY_ONLY'}
            return {'feedback_id': self.repo.append(c, case['case_id'], 'feedback', event), 'learning_status': 'TELEMETRY_ONLY'}
        elif operation == 'exports':
            if payload.get('snapshot_id') != case['snapshot_id'] or payload.get('mode') not in ('ANNOTATED','REVIEWED'):
                raise PatentError('EXPORT_SNAPSHOT', '현재 산출물 버전과 내보내기 종류를 확인해야 합니다.')
            data, manifest = forms.render(case, material, payload['mode'], self.current_reviews(owner, case, c), self.runtime_checks(owner, case, material, c), self.sample_image(owner, case, material, c))
            if payload.get('manifest_hash') != manifest['manifest_hash']:
                return {'manifest': manifest, 'requires_manifest_confirmation': True}
            export_id = ident('pex')
            self.put_asset(c, case, export_id, 'patent-draft.zip', 'application/zip', data)
            self.repo.append(c, case['case_id'], 'export', {'asset_id': export_id, 'manifest': manifest}, record_id=export_id)
            return {'export_id': export_id, 'manifest': manifest}
        else:
            raise PatentError('OPERATION_UNKNOWN', '지원하지 않는 사건 작업입니다.', 422)
        return {'ok': True}

    def put_asset(self, c, case, asset_id, name, mime, content):
        if len(content) > 20_000_000:
            raise PatentError('ASSET_TOO_LARGE', '첨부 또는 출력이 20MB를 초과합니다.', 422)
        c.execute(insert(assets).values(asset_id=asset_id, case_id=case['case_id'], name=name, mime=mime,
                                       sha256=hashlib.sha256(content).hexdigest(), content=content))

    def issue(self, c, case, tool, role=None, payload=None):
        if tool not in OPERATIONS:
            raise PatentError('TOOL_UNKNOWN', '허용되지 않는 특허 도구입니다.', 422)
        tier, kind, _ = OPERATIONS[tool]
        if tool == 'patent_review_content' and role not in ROLES[:2] or tool == 'patent_final_review' and role != 'GLOBAL_FINAL':
            raise PatentError('REVIEW_ROLE', '필수 검토 역할을 변경할 수 없습니다.')
        readset = self.readset(case, role)
        reservation, reserved = None, 0
        if tier != 'CODE':
            profile = ModelProfile.pinned(case['model_config'])
            if tier not in profile.models:
                raise PatentError('REVIEW_MODEL_UNAVAILABLE', '특허 모델 설정이 없습니다.', 503)
            reserved = reserve(case['budget'], profile.models[tier], is_review=tier == 'T3')
            reservation = ident('pbr')
        task_id = ident('ptask')
        payload_ref = self.repo.append(c, case['case_id'], 'task_payload', payload or {})
        ticket = TaskTicket(task_id=task_id, case_id=case['case_id'], epoch=case['epoch'], input_snapshot_id=case['snapshot_id'],
            input_hash=digest(readset), rule_pack_version=case['rulepack_version'], model_profile=PROFILE,
            policy_version=case['policy_version'], scope_policy_version=SCOPE, read_version_ids=readset,
            idempotency_key=task_id, operation_payload_ref=payload_ref, tool_name=tool, tier=tier,
            review_role=role, budget_reservation_id=reservation).model_dump()
        c.execute(insert(tasks).values(task_id=task_id, case_id=case['case_id'], status='QUEUED', lease_until_ms=0,
            fence=0, body=canonical({'ticket': ticket, 'reserved_micro_usd': reserved, 'attempts': 0})))
        from .learning import govern_operation
        self.repo.append(c,case['case_id'],'governor_decision',{
            'task_id':task_id,'ticket_hash':digest(ticket),'policy_version':case['policy_version'],
            **govern_operation(tool)})
        return {'task_id': task_id, 'ticket': ticket}

    def plan(self, c, owner, case):
        if case['execution_status'] not in ('QUEUED','RUNNING','WAITING_HUMAN'):
            return
        self.retire_stale_queued(c, case)
        if c.execute(select(tasks.c.task_id).where(tasks.c.case_id == case['case_id'], tasks.c.status.in_(['QUEUED','RUNNING']))).first():
            return
        material = self.material(owner, case, c)
        approvals = self.approvals(owner, case, c)
        if not intake_complete(material):
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'APPLICATION_CONTEXT'
            return
        if unanswered(material):
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'QUESTIONS'
            return
        sequence = [('invention','patent_extract_invention'), ('questions','patent_plan_questions'),
            ('search_plan','patent_plan_search'), ('sources','patent_search_local'), ('claim_chart','patent_build_claim_chart')]
        for kind, operation in sequence:
            if kind not in material:
                self.issue(c, case, operation)
                case['execution_status'] = 'QUEUED'
                return
        if approvals.get('G1') != digest(material['invention']):
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'G1'
            return
        if 'claims' not in material:
            self.issue(c, case, 'patent_draft_claims')
            return
        if approvals.get('G2') != digest(material['claims']):
            case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'G2'
            return
        for kind, operation in [('specification','patent_draft_specification'), ('drawings','patent_build_drawings')]:
            if kind not in material:
                self.issue(c, case, operation)
                return
        current = {r['role']: r for r in self.current_reviews(owner, case, c)}
        from .coverage import delivery_scope
        scope=delivery_scope(case,material)
        if not any(r.get('scope')==scope for r in self.repo.records(owner,case['case_id'],'delivery_scope',c)):
            self.repo.append(c,case['case_id'],'delivery_scope',{'scope':scope,'content_manifest_hash':digest(scope)})
        for role in ROLES[:2]:
            if role not in current:
                self.issue(c, case, 'patent_review_content', role)
                return
        issues = [f for r in self.current_reviews(owner, case, c) if r['role'] in ROLES
                  for f in r['findings'] if f['outcome'] in ('FAIL','UNKNOWN')]
        issues.extend({'rule_id':'CONTENT_TARGET','outcome':f['outcome'],
                       'explanation':f['explanation'],'target_id':f['target_id'],
                       'affected_artifacts':r['covered_artifact_ids']}
                      for r in self.current_reviews(owner,case,c) if r['role'] in ROLES
                      for f in r.get('target_checks',[]) if f['outcome'] in ('FAIL','UNKNOWN'))
        if issues:
            if case['repair_rounds'] < 2:
                self.issue(c, case, 'patent_reconcile_issues', payload={'issues': issues})
                case['repair_rounds'] += 1
            else:
                case['execution_status'], case['waiting_for'] = 'WAITING_HUMAN', 'OPEN_ISSUES'
            return
        if 'GLOBAL_FINAL' not in current:
            self.issue(c, case, 'patent_final_review', 'GLOBAL_FINAL')
            return
        checks = self.runtime_checks(owner, case, material, c)
        attachments_complete=all(d.get('parse_status')=='TEXT_EXTRACTED' for d in material.get('attachments',{}).get('documents',[]))
        ready = attachments_complete and all(r['outcome'] in ('PASS','NOT_APPLICABLE') for r in checks if r['severity'] == 'BLOCKER') and all(
            f['outcome'] in ('PASS','NOT_APPLICABLE') for r in self.current_reviews(owner, case, c)
            for f in [*r['findings'],*r.get('target_checks',[])])
        case['document_status'] = 'DRAFT_READY' if ready else 'DRAFT_WITH_OPEN_ISSUES'
        case['execution_status'] = 'COMPLETED' if ready else 'WAITING_HUMAN'
        case['waiting_for'] = None if ready else 'OPEN_ISSUES'

    def task(self, owner, case_id, task_id):
        self.repo.get(owner, case_id)
        with self.repo.engine.connect() as c:
            row = c.execute(select(tasks).where(tasks.c.task_id == task_id, tasks.c.case_id == case_id)).mappings().first()
        if not row:
            raise PatentError('NOT_FOUND', '작업을 찾을 수 없습니다.', 404)
        return {'task_id': task_id, 'status': row['status'], **json.loads(row['body'])}

    def execute(self, owner, ticket):
        from .access import require_tester
        require_tester(self.legacy,owner)
        ticket = TaskTicket.model_validate(ticket).model_dump()
        case_id, task_id = ticket['case_id'], ticket['task_id']
        with self.repo.engine.begin() as c:
            case = self.repo.get(owner, case_id, c, lock=True)
            row = c.execute(select(tasks).where(tasks.c.task_id == task_id, tasks.c.case_id == case_id).with_for_update()).mappings().first()
            if not row or json.loads(row['body'])['ticket'] != ticket:
                raise PatentError('TASK_TICKET_INVALID', '서버가 발급한 작업표와 일치하지 않습니다.', 403)
            body = json.loads(row['body'])
            if row['status'] in ('COMPLETED','FAILED','STALE','UNCERTAIN','CANCELLED'):
                return {'task_id': task_id, 'status': row['status'], 'result': body.get('result')}
            if os.getenv('PATENT_DISPATCH_ENABLED', 'false').lower() != 'true':
                raise PatentError('DISPATCH_DISABLED', '특허 실행이 비활성화됐습니다.', 503)
            if row['status'] != 'QUEUED' or case['execution_status'] in ('CANCELLED','PAUSED_USER','PAUSED_BUDGET','PAUSED_DEPENDENCY'):
                raise PatentError('TASK_NOT_RUNNABLE', '현재 실행할 수 없는 작업입니다.')
            if case['epoch'] != ticket['epoch'] or set(ticket['read_version_ids']) != set(self.readset(case, ticket['review_role'])):
                raise PatentError('TASK_STALE', '입력 자료가 변경된 작업입니다.')
            if OPERATIONS[ticket['tool_name']][0] != 'CODE' and (not intake_complete(self.material(owner, case, c)) or unanswered(self.material(owner, case, c))):
                raise PatentError('QUESTIONS_REQUIRED', '필수 사용자 입력이 완료되지 않았습니다.')
            fence = row['fence'] + 1
            claimed = c.execute(update(tasks).where(tasks.c.task_id == task_id, tasks.c.status == 'QUEUED', tasks.c.fence == row['fence'])
                .values(status='RUNNING', fence=fence, lease_until_ms=now()+360_000))
            if claimed.rowcount != 1:
                raise PatentError('TASK_ALREADY_RUNNING', '이미 실행 중인 작업입니다.')
            self.repo.append(c,case_id,'execution_guard',{'task_id':task_id,'ticket_hash':digest(ticket),
                'fence':fence,'epoch':case['epoch'],'dispatch_enabled':True,
                'read_version_ids':ticket['read_version_ids']})
            material = self.material(owner, case, c, ticket['input_snapshot_id'])
            payload_record = self.repo.record(owner, case_id, ticket['operation_payload_ref'], c)
            payload = {k: v for k, v in payload_record.items() if k not in ('id','kind')}
            version_to_kind = {v: k for k, v in case['artifacts'].items()}
            context = {version_to_kind[v]: material[version_to_kind[v]] for v in ticket['read_version_ids']}
            context['snapshot_id'] = ticket['input_snapshot_id']
            context['read_version_ids'] = ticket['read_version_ids']
            context['artifact_versions']={kind:v for kind,v in case['artifacts'].items() if v in ticket['read_version_ids']}
            if ticket['tool_name'] == 'patent_reconcile_issues':
                context['issues'] = payload['issues']
            role = ticket['review_role']
            if role == 'GLOBAL_FINAL':
                context['independent_reviews'] = self.current_reviews(owner, case, c)
            if role:
                context['rule_obligations'] = rules.obligations(role)
                from .coverage import targets
                context['review_targets']=targets(material,context['artifact_versions'])
            revision = case['revision']
            case['execution_status'] = 'RUNNING'
            self.repo.save(c, case, revision)
        # Network / CPU work happens after releasing every database transaction.
        tier, kind, schema = OPERATIONS[ticket['tool_name']]
        charge, result, error, provider_receipt = 0, None, None, None
        try:
            if tier != 'CODE':
                model = ModelProfile.pinned(case['model_config']).models[tier]
                instruction = INSTRUCTIONS.get(kind, '')
                if role:
                    instruction = ('Independently review every listed obligation and every material artifact. '
                        'Return exactly one finding per rule_id, all covered artifact version IDs and input snapshot. '
                        'Do not treat missing evidence as PASS. NOT_APPLICABLE requires actual inapplicability evidence. '
                        'For each semantic PASS/FAIL/NOT_APPLICABLE, cite source_spans with artifact_id, JSON pointer within that artifact and an exact excerpt (8-3000 characters). '
                        'evidence_ids and affected_artifacts refer only to input artifact version IDs. ID presence alone does not prove semantic support. '
                        'Return one target_check for every review_targets entry, preserving its target_id and content_hash. Check each claim, effect, paragraph and drawing; missing evidence is UNKNOWN. '
                        'Use role '+role+'. '+('Review technical/engineering content without peer verdicts.' if role == ROLES[0] else
                        'Review patent content independently.' if role == ROLES[1] else 'Perform final whole-package consistency review.'))
                charge = None  # Unknown until usage response; every failed attempt retains reservation.
                response = self.gateway.generate(model, instruction, context, schema.model_json_schema())
                charge = response['cost_micro_usd']
                provider_receipt={k:response[k] for k in ('usage','provider_request_id','provider_model','boundary_contract') if k in response}
                if response.get('error'):
                    raise PatentError(response['error'], '모델 출력이 완성되지 않았습니다.', 503)
                result = schema.model_validate(response['value']).model_dump()
                if kind == 'invention':
                    for feature in result['features']:
                        feature['provenance'] = 'DERIVED_PROPOSAL'
                    for effect in result['effects']:
                        effect['evidence_status'] = 'HYPOTHESIS'
                if kind=='drawings':
                    features={f['id'] for f in material.get('invention',{}).get('features',[])}
                    if any(n['feature_id'] not in features for d in result['drawings'] for n in d['nodes']):
                        raise PatentError('DRAWING_REFERENCE_INVALID','도면에 발명정보에 없는 구성요소가 포함됐습니다.',503)
                if kind == 'reconciliation' and result['questions']:
                    Questions.model_validate({'questions': result['questions']})
                    existing_ids = {q['id'] for q in material.get('questions', {}).get('questions', [])}
                    if existing_ids & {q['id'] for q in result['questions']}:
                        raise PatentError('QUESTION_ID_CONFLICT', '추가 질문이 기존 질문을 덮어쓸 수 없습니다.')
                if role:
                    expected = {r['rule_id'] for r in rules.obligations(role)}
                    ids = [f['rule_id'] for f in result['findings']]
                    if result['role'] != role or result['input_snapshot_id'] != ticket['input_snapshot_id'] or set(result['covered_artifact_ids']) != set(ticket['read_version_ids']) or set(ids) != expected or len(ids) != len(set(ids)):
                        raise PatentError('REVIEW_COVERAGE_INVALID', '필수 규칙 또는 산출물의 검토 범위가 누락됐습니다.', 503)
                    from .coverage import validate as validate_targets
                    validate_targets(result['target_checks'],context['review_targets'])
                    for f in result['findings']:
                        from .review_evidence import validate as validate_evidence
                        validate_evidence(f,material,version_to_kind,ticket['read_version_ids'],bool(rules.RULES[f['rule_id']]['semantic_roles']))
                        if f['severity'] != rules.RULES[f['rule_id']]['severity']:
                            raise PatentError('REVIEW_SEVERITY_INVALID', '검토자가 필수 규칙의 심각도를 변경했습니다.', 503)
                        if f['outcome'] == 'NOT_APPLICABLE' and (rules.applicability(f['rule_id'], case, material) is not False or not f['evidence_ids']):
                            raise PatentError('REVIEW_NA_INVALID', '적용 제외의 근거가 없거나 제외할 수 없는 규칙입니다.', 503)
            elif kind == 'sources':
                result = self.sources.local(material['search_plan']['queries'], material['source'].get('references', []))
            elif kind == 'source_detail':
                result = self.sources.enrich(payload['application_number'], payload['issue_id'], payload['missing_fields'])
            elif kind == 'checks':
                result = {'checks': self.runtime_checks(owner, case, material)}
            elif kind == 'feedback':
                result = feedback_event(case, payload)
            elif kind == 'export':
                data, manifest = forms.render(case, material, payload.get('mode'),
                    self.current_reviews(owner, case), self.runtime_checks(owner, case, material), self.sample_image(owner, case, material))
                if payload.get('manifest_hash') != manifest['manifest_hash'] or payload.get('snapshot_id') != case['snapshot_id']:
                    raise PatentError('EXPORT_CONFIRMATION_REQUIRED', '내보내기는 정확한 manifest 승인이 필요합니다.')
                result = {'manifest': manifest}
            elif kind == 'patch':
                proposal = self.repo.record(owner, case_id, payload.get('patch_id'))
                if proposal['kind'] != 'patch_proposal' or payload.get('approved_by') != owner:
                    raise PatentError('PATCH_APPROVAL_REQUIRED', '수정 제안은 owner의 버전 확인 후 적용해야 합니다.')
                result = {'patch_id': proposal['id']}
        except ValidationError:
            error = 'OUTPUT_SCHEMA_INVALID'
        except PatentError as exc:
            error = exc.code
            if exc.code in ('PROVIDER_NOT_ALLOWED','REVIEW_COVERAGE_LIMIT'):
                charge = 0
        except Exception:
            error = 'TASK_DEPENDENCY_FAILED'
        with self.repo.engine.begin() as c:
            current = self.repo.get(owner, case_id, c, lock=True)
            row = c.execute(select(tasks).where(tasks.c.task_id == task_id).with_for_update()).mappings().one()
            if row['fence'] != fence or row['status'] != 'RUNNING':
                raise PatentError('LEASE_LOST', '작업 임대가 만료됐습니다. 비용 확인이 필요합니다.')
            settle(current['budget'], body['reserved_micro_usd'], charge)
            if tier=='T3' and charge==0 and error in ('PROVIDER_NOT_ALLOWED','REVIEW_COVERAGE_LIMIT') and current['execution_status']!='CANCELLED':
                current['budget']['review_plan_micro_usd']+=body['reserved_micro_usd']
            if provider_receipt:
                self.repo.append(c,case_id,'provider_receipt',{'task_id':task_id,**provider_receipt})
            self.repo.append(c, case_id, 'cost', {'task_id': task_id, 'reservation_id': ticket['budget_reservation_id'],
                'reserved_micro_usd': body['reserved_micro_usd'], 'actual_micro_usd': charge,
                'status': 'UNKNOWN' if charge is None else 'ACCOUNTED', 'tier': tier})
            stale = current['epoch'] != ticket['epoch'] or set(ticket['read_version_ids']) != set(self.readset(current, ticket['review_role'])) or current['execution_status'] in ('CANCELLED','PAUSED_USER')
            status = 'STALE' if stale else 'UNCERTAIN' if charge is None else 'FAILED' if error else 'COMPLETED'
            if not stale and not error:
                if kind == 'review':
                    result = {**result, 'tier': 'T3', 'epoch': ticket['epoch'], 'model_profile': PROFILE, 'task_id': task_id,
                              'read_version_ids': ticket['read_version_ids'], 'model_config_hash': digest(current['model_config'])}
                    self.repo.append(c, case_id, 'review', result)
                elif kind == 'reconciliation':
                    for proposal in result['proposals']:
                        self.repo.append(c, case_id, 'patch_proposal', proposal)
                    self.repo.append(c, case_id, 'reconciliation', result)
                    if result['questions']:
                        values = {'questions': result['questions']}
                        self.repo.artifact(c, current, 'review_questions', values, ticket['read_version_ids'], producer=ticket['tool_name'])
                    current['execution_status'], current['waiting_for'] = 'WAITING_HUMAN', 'PATCH_REVIEW'
                elif kind == 'export':
                    export_id = ident('pex')
                    self.put_asset(c, current, export_id, 'patent-draft.zip', 'application/zip', data)
                    self.repo.append(c, case_id, 'export', {'asset_id': export_id, 'manifest': manifest}, record_id=export_id)
                elif kind == 'patch':
                    self.reduce(c, owner, current, 'apply-patch', result)
                elif kind in MATERIAL_TYPES:
                    if kind=='source_detail':
                        documents=dict(self.material(owner,current,c).get('source_detail',{}).get('documents',{}))
                        documents[result['application_number']]=result
                        result={'documents':documents}
                    self.repo.artifact(c, current, kind, result, ticket['read_version_ids'], producer=ticket['tool_name'])
                    if kind == 'sources':
                        current['evidence_status'] = result['status']
                else:
                    self.repo.append(c, case_id, kind, result)
            elif not stale:
                current['execution_status'] = 'PAUSED_DEPENDENCY'
                current['last_error'] = error or 'USAGE_UNKNOWN'
            body['result'] = {'error_code': error, 'charged_micro_usd': charge}
            c.execute(update(tasks).where(tasks.c.task_id == task_id, tasks.c.fence == fence)
                      .values(status=status, body=canonical(body), lease_until_ms=0))
            should_plan = (not stale and not error and kind != 'reconciliation') or (stale and current['execution_status'] == 'QUEUED')
            if should_plan:
                # An owner may resume changed input while its old call is still
                # running. Once that stale attempt settles, schedule the new input.
                current['execution_status'] = 'QUEUED'
                try:
                    self.plan(c, owner, current)
                except PatentError as exc:
                    if 'BUDGET' in exc.code:
                        current['execution_status'], current['last_error'] = 'PAUSED_BUDGET', exc.code
                    else:
                        raise
            self.repo.save(c, current, current['revision'])
            self.repo.append(c, case_id, 'event', {'type': 'TASK_'+status, 'task_id': task_id,
                                                'revision': current['revision'], 'epoch': current['epoch']})
        return {'task_id': task_id, 'status': status, 'result': body['result']}

    def recover_expired(self):
        with self.repo.engine.connect() as c:
            expired = c.execute(select(tasks.c.task_id, tasks.c.case_id).where(tasks.c.status == 'RUNNING', tasks.c.lease_until_ms < now())).all()
        for task_id, case_id in expired:
            with self.repo.engine.begin() as c:
                row = c.execute(select(cases).where(cases.c.case_id == case_id).with_for_update()).mappings().one()
                case = json.loads(row['body'])
                task = c.execute(select(tasks).where(tasks.c.task_id == task_id).with_for_update()).mappings().one()
                if task['status'] != 'RUNNING' or task['lease_until_ms'] >= now():
                    continue
                body = json.loads(task['body'])
                settle(case['budget'], body['reserved_micro_usd'], None)
                if case['execution_status'] not in ('CANCELLED','PAUSED_USER'):
                    case['execution_status'], case['last_error'] = 'PAUSED_DEPENDENCY', 'UNCERTAIN_CALL_AFTER_RESTART'
                self.repo.append(c, case_id, 'cost', {'task_id': task_id,
                    'reservation_id': body['ticket']['budget_reservation_id'],
                    'reserved_micro_usd': body['reserved_micro_usd'], 'actual_micro_usd': None,
                    'status': 'UNKNOWN_AFTER_LEASE_EXPIRY', 'tier': body['ticket']['tier']})
                c.execute(update(tasks).where(tasks.c.task_id == task_id).values(status='UNCERTAIN', fence=task['fence']+1))
                self.repo.save(c, case, case['revision'])
