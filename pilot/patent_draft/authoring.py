"""Typed inter-stage reasoning artifacts and traceable drafting vocabulary."""
from typing import Literal
from pydantic import Field, model_validator
from .domain import Strict, Question, PatentError


class EvidenceRef(Strict):
    artifact: str = Field(description='Exact top-level input artifact key; copy from evidence_catalog when available.')
    pointer: str = Field(description='JSON Pointer to a string leaf inside that artifact. Arrays use zero-based numeric indexes. Copy the catalog pointer verbatim, never point to a whole object/list.')
    excerpt: str = Field(min_length=1, max_length=3000, description='Exact contiguous original text at pointer. Never summarize, translate, join separate fields, or add ellipses. Copy a catalog excerpt verbatim.')


class ReasonedFact(Strict):
    id: str
    statement: str = Field(min_length=1)
    category: Literal['PROBLEM','COMPONENT','MECHANISM','CONSTRAINT','EFFECT','RISK']
    status: Literal['SOURCE_PROPOSAL','USER_REPORTED','INFERRED','UNKNOWN']
    basis: list[EvidenceRef] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class SolutionChange(Strict):
    subject: str
    before: str
    after: str
    reason: str
    basis: list[EvidenceRef] = Field(min_length=1)


class SynthesisIssue(Strict):
    id: str
    description: str
    resolution: str
    status: Literal['RESOLVED','OPEN']
    blocking: bool
    question_id: str | None = None


class SynthesizedSolution(Strict):
    title: str
    problem: str
    revised_solution: str = Field(min_length=1)
    working_principle: str = Field(min_length=1)
    changes: list[SolutionChange]
    facts: list[ReasonedFact] = Field(min_length=1)
    issues: list[SynthesisIssue]
    questions: list[Question] = Field(max_length=3)

    @model_validator(mode='after')
    def coherent(self):
        if len({f.id for f in self.facts}) != len(self.facts):
            raise ValueError('duplicate synthesis fact IDs')
        question_ids={q.id for q in self.questions if q.blocking}
        if any(i.blocking and i.status=='OPEN' and i.question_id not in question_ids for i in self.issues):
            raise ValueError('unresolved blocking synthesis issue requires an explicit question')
        if any(q.id.startswith('APPLICATION_') for q in self.questions):
            raise ValueError('synthesis cannot overwrite delta intake')
        return self


class DraftingKeyword(Strict):
    id: str = Field(min_length=1, max_length=160)
    term: str = Field(min_length=1, max_length=200)
    category: Literal['PROBLEM','COMPONENT','MECHANISM','CONSTRAINT','EFFECT','RISK']
    definition: str = Field(min_length=1)
    synonyms: list[str]
    fact_ids: list[str] = Field(min_length=1)
    target_sections: list[str] = Field(min_length=1)
    rationale: str = Field(min_length=1)


class DraftingKeywords(Strict):
    keywords: list[DraftingKeyword] = Field(min_length=1, max_length=60)
    terminology_rules: list[str]

    @model_validator(mode='after')
    def unique(self):
        if len({k.id for k in self.keywords})!=len(self.keywords):
            raise ValueError('duplicate keyword IDs')
        return self


class CoherenceCheck(Strict):
    id: str
    dimension: Literal['PROBLEM_SOLUTION','MECHANISM_EFFECT','CLAIM_SUPPORT','TERMINOLOGY','CONTEXT_FLOW','DRAWING_ALIGNMENT']
    outcome: Literal['PASS','FAIL','UNKNOWN']
    explanation: str = Field(min_length=1)
    basis: list[EvidenceRef] = Field(min_length=1)
    affected_sections: list[str]
    repair_instruction: str


class DocumentCoherence(Strict):
    summary: str
    checks: list[CoherenceCheck] = Field(min_length=6)

    @model_validator(mode='after')
    def coverage(self):
        required={'PROBLEM_SOLUTION','MECHANISM_EFFECT','CLAIM_SUPPORT','TERMINOLOGY','CONTEXT_FLOW','DRAWING_ALIGNMENT'}
        if {c.dimension for c in self.checks} != required or len({c.id for c in self.checks})!=len(self.checks):
            raise ValueError('all document flow dimensions must be checked')
        return self


def validate_basis(ref, context):
    value=context.get(ref['artifact'])
    try:
        if ref['pointer']:
            if not ref['pointer'].startswith('/'):
                raise ValueError()
            for key in ref['pointer'][1:].split('/'):
                key=key.replace('~1','/').replace('~0','~')
                value=value[int(key)] if isinstance(value,list) else value[key]
        if not isinstance(value,str) or ref['excerpt'] not in value:
            raise ValueError()
    except (KeyError,IndexError,TypeError,ValueError):
        raise PatentError('AUTHORING_EVIDENCE_INVALID','단계별 분석 근거가 실제 입력과 일치하지 않습니다.',503) from None


def evidence_catalog(context, limit=160):
    """Deterministic citation coordinates; every excerpt still passes strict validation."""
    result=[]
    def visit(artifact,value,pointer=''):
        if len(result)>=limit:return
        if isinstance(value,str) and value.strip():
            result.append({'artifact':artifact,'pointer':pointer,'excerpt':value[:2000]})
        elif isinstance(value,dict):
            for key,item in value.items():
                if key in {'confirmed_by','scope_note','source_hash','legacy_state_hash','raw_publication'}:continue
                visit(artifact,item,pointer+'/'+key.replace('~','~0').replace('/','~1'))
        elif isinstance(value,list):
            for i,item in enumerate(value):visit(artifact,item,pointer+'/'+str(i))
    for name in ('application_context','answers','facts','specification','claims','drawings','invention','synthesized_solution','source','attachments'):
        if name in context:visit(name,context[name])
    return result


def validate_result(kind, result, context):
    if kind=='synthesized_solution':
        for item in [*result['facts'],*result['changes']]:
            for ref in item['basis']:
                validate_basis(ref,context)
    elif kind=='drafting_keywords':
        fact_ids={f['id'] for f in context['synthesized_solution']['facts']}
        sections={s['id'] for s in context['drafting_template']['sections']} | {'claims','abstract','drawings'}
        if any(set(k['fact_ids'])-fact_ids or set(k['target_sections'])-sections for k in result['keywords']):
            raise PatentError('KEYWORD_LINEAGE_INVALID','키워드가 존재하지 않는 분석 근거나 문서 항목을 가리킵니다.',503)
    elif kind=='document_coherence':
        for check in result['checks']:
            for ref in check['basis']:
                validate_basis(ref,context)
    elif kind=='invention' and 'synthesized_solution' in context:
        facts={f['id'] for f in context['synthesized_solution']['facts']}
        if any(not f['source_ids'] or set(f['source_ids'])-facts for f in result['features']):
            raise PatentError('INVENTION_LINEAGE_INVALID','발명 구성요소가 수정 해결안의 기술 사실과 연결되지 않았습니다.',503)
    elif kind=='specification' and 'drafting_keywords' in context:
        ids={k['id'] for k in context['drafting_keywords']['keywords']} | {f['id'] for f in context['synthesized_solution']['facts']}
        if any(s['id']!='title' and s['text'] and (not s['source_ids'] or set(s['source_ids'])-ids) for s in result['sections']):
            raise PatentError('SPECIFICATION_LINEAGE_INVALID','명세서 항목의 분석 근거나 키워드 연결이 누락됐습니다.',503)
