"""Readable output vocabulary; never rewrite stored values, URLs or program code."""
import re

TERMS={
    'QUICK_WIN':'QUICK WIN','BIG_BET':'BIG BET','FILL_IN':'FILL IN',
    'PARAMETER':'파라미터 조정','PARTIAL':'국부적 변경','REDESIGN':'구조 재설계',
    'PHYSICAL_TECHNICAL':'물리·공학 문제','INFORMATION_SOFTWARE':'정보·소프트웨어 문제',
    'ORGANIZATIONAL_BUSINESS':'조직·비즈니스 문제','MUST_HAVE':'필수 조건','MUST_NOT_HAVE':'금지 조건',
    'TARGET_DISADVANTAGE':'목표로 삼은 문제 현상','ROOT_CAUSE':'근본 원인','KEY_DISADVANTAGE':'핵심 문제 현상',
    'ENG_39':'공학 변수 39개','BIZ_31':'비즈니스 변수 31개','LLM_FALLBACK':'모델 기반 보완',
    'USER_REPORTED':'사용자 진술','USER_REPORTED_NOT_MEASUREMENT':'사용자 진술·실측 미확인',
    'DERIVED_PROPOSAL':'새 기술 제안','USER_CONFIRMED':'사용자 확인',
    'NOT_RUN':'미실행','NOT_STARTED':'시작 전','WAITING_HUMAN':'사용자 입력 대기',
    'DRAFT_WITH_OPEN_ISSUES':'미해결 사항이 있는 초안','DRAFT_READY':'필수 검토를 마친 초안',
    'TECHNICAL_CONTENT':'기술내용 검토','PATENT_CONTENT':'특허내용 검토','GLOBAL_FINAL':'최종 일관성 검토',
    'TELEMETRY_ONLY':'기록 수집·학습 미연계','NOT_APPLICABLE':'해당 없음',
    'TITLE_ABSTRACT_ONLY':'제목·초록만 확보','DETAIL_FIELDS_ONLY':'상세 서지정보 범위',
    'FILING_CANDIDATE':'출원도면 후보','CONCEPT_IMAGE':'참고용 이미지',
    'SAME_DOMAIN':'동일 분야 접근','CROSS_DOMAIN':'타산업 이식','PROTOTYPE_KNOWN':'시작품·문헌 확인',
    'PROVEN_ELSEWHERE':'타산업 검증','COMMERCIAL_ELSEWHERE':'타산업 상용화','COMMERCIAL_SAME':'동종업계 상용화',
    'CONCEPT_ONLY':'개념 단계','MODEL_KNOWLEDGE':'모델 지식','INTERNAL_FEEDBACK':'내부 피드백',
    'MATERIAL_COMPAT':'재료 양립성','USER_STATED':'사용자 명시','SYSTEM_LEVEL':'시스템 계층',
    'IN_SYSTEM':'시스템 내부','IN_SUPERSYSTEM':'상위 시스템','IN_ENVIRONMENT':'주변 환경','LOW_COST':'저비용',
    'MISSING_S2':'도구 누락','MISSING_F':'장 누락','USEFUL_SUFFICIENT':'유익·충분','USEFUL_INSUFFICIENT':'유익·부족',
    'UNVERIFIED':'미검증','HYPOTHESIS':'가설','OBSERVED':'관측 근거','MEASURED':'실측 근거',
    'COVERAGE_GAP':'검토 범위 누락','MISSING_TRANSFER_PATH':'작동 경로 미작성','INCOMPLETE_TEST_PLAN':'시험 계획 미완성',
    'S0_RESEARCH':'산업·기술 심층 검토','S7_GATE':'제약 검토',
}
FIELDS={
    'change_scale':'변경 범위','novelty_class':'접근 분야','quality_status':'검토 상태',
    'evidence_status':'근거 수준','evidence_scope':'근거 범위','source_type':'출처 유형',
    'working_principle':'작동 원리','expected_effect':'기대 효과','validation_plan':'검증 계획',
    'transfer_conditions':'적용 조건','required_resources':'필요 자원','changes_to_system':'시스템 변경사항',
    'open_risks':'예상 위험','risk_level':'위험 수준','return_level':'기대효과 수준',
    'feasibility_hint':'구현 가능성','resolution_status':'모순 해소 상태','operating_scope':'운전 범위',
    'intervention_variable':'개입 변수','changed_variable':'변화하는 물리량','mediating_functions':'매개 기능',
    'resolution_argument':'모순 해소 근거','concept_review':'개념 검토','constraint_verdict':'제약 판정',
    'test_preparation':'시험 준비','structural_status':'구조 검토','quality_issues':'검토 쟁점',
    'test_method':'시험 방법','acceptance_criteria':'통과 기준','measurement_method':'측정 방법',
    'technical_review':'기술 검토','editor_validation':'공식 작성기 검증','fulltext_coverage':'원문 확보 범위',
}
_FIELDS=re.compile(r'(?<![A-Za-z0-9_])(?:[\"\x27])?('+ '|'.join(FIELDS)+r')(?:[\"\x27])?\s*[:=]\s*')
_PROTECTED=re.compile(r'(```[\s\S]*?```|~~~[\s\S]*?~~~|https?://[^\s<>\[\]\"\x27]+|<[^>]*>)')


def display_text(value,extra=None):
    terms={**(extra or {}),**TERMS}
    pattern=re.compile(r'(?<![A-Za-z0-9_])('+ '|'.join(re.escape(k) for k in sorted(terms,key=len,reverse=True))+r')(?![A-Za-z0-9_])',re.I)
    lookup={k.casefold():v for k,v in terms.items()}
    def prose(text):
        text=_FIELDS.sub(lambda m:FIELDS[m[1]]+': ',text)
        return pattern.sub(lambda m:lookup[m[0].casefold()],text)
    def chunk(text):
        # Internal badges are sometimes quoted as inline code. Render those as
        # prose while leaving actual variable names and formulas untouched.
        parts=re.split(r'(`[^`\n]+`)',text)
        return ''.join(prose(p[1:-1]) if i%2 and (p[1:-1] in terms or _FIELDS.search(p[1:-1]))
                       else p if i%2 else prose(p) for i,p in enumerate(parts))
    return ''.join(p if i%2 else chunk(p) for i,p in enumerate(_PROTECTED.split(str(value or ''))))


def display_value(value):
    if isinstance(value,dict):
        return ' · '.join(f'{FIELDS.get(k,k.replace("_"," "))}: {display_value(v)}' for k,v in value.items())
    if isinstance(value,(list,tuple)):
        return ' · '.join(display_value(v) for v in value)
    if value is None:return '미확인'
    if isinstance(value,bool):return '예' if value else '아니요'
    return display_text(value)
