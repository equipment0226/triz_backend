"""Mandatory owner input after selecting an idea, before technical drafting."""
from .domain import PatentError

APPLICATION_QUESTIONS = [
    {'id':'APPLICATION_CHANGES','question':'아이디어를 실제로 적용하면서 바뀌는 구성·동작·사용 조건은 무엇인가요?',
     'reason':'선택한 아이디어와 실제 발명 사이의 변경사항을 초안에 반영합니다.',
     'affected_fields':['invention','claims','specification','drawings'],'blocking':True},
    {'id':'APPLICATION_CONSTRAINTS','question':'실제 적용 시 반드시 지켜야 할 제약조건은 무엇인가요?',
     'reason':'성능·치수·재료·운전환경·비용 등 적용 조건을 확인합니다. 없거나 미확인인 경우도 직접 적어 주세요.',
     'affected_fields':['invention','claims','specification'],'blocking':True},
    {'id':'APPLICATION_RISKS','question':'예상되는 위험·부작용·미검증 사항과 추가 수정 필요성이 있나요?',
     'reason':'해결되지 않은 위험을 확인 사실로 쓰지 않고, 보강 질문과 검토 항목으로 유지합니다.',
     'affected_fields':['invention','claims','specification','drawings'],'blocking':True},
]


def complete(material):
    value = material.get('application_context', {})
    return bool(value.get('confirmed_by') and all(isinstance(value.get(q['id']), str) and value[q['id']].strip()
                                                 for q in APPLICATION_QUESTIONS))


def questions(material):
    return (material.get('application_questions', {}).get('questions', APPLICATION_QUESTIONS)
            + material.get('questions', {}).get('questions', [])
            + material.get('review_questions', {}).get('questions', []))


def unanswered(material):
    answers = material.get('answers', {})
    return [q for q in questions(material) if q.get('blocking', True)
            and not str(answers.get(q['id'], '')).strip()]


def context_from_answers(owner, existing, answers):
    values = dict(existing)
    for question in APPLICATION_QUESTIONS:
        if question['id'] in answers:
            value = answers[question['id']]
            if not isinstance(value, str) or not value.strip() or len(value) > 8000:
                raise PatentError('APPLICATION_CONTEXT_REQUIRED', '변경사항·제약조건·위험요소를 모두 직접 입력해 주세요.', 422)
            values[question['id']] = value.strip()
    values['confirmed_by'] = owner
    values['evidence_status'] = 'USER_REPORTED_NOT_MEASUREMENT'
    return values
