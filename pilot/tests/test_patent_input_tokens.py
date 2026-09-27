"""Regression: Korean JSON bytes are not model tokens; no material is omitted."""
from dataclasses import replace
import json
import httpx
import pytest
from patent_draft.domain import PatentError, canonical, digest
from patent_draft.models import Gateway, Model
from patent_draft import input_tokens


def model(name='deepseek-flash', limit=262144):
    return Model('T2', name, 'https://api.deepseek.com/v1', 'PATENT_TEST_KEY', '.3', '1.2', limit, 8192)


@pytest.mark.parametrize('name', ['deepseek-flash', 'deepseek-v4-pro'])
def test_full_korean_material_above_old_byte_limit_reaches_provider(name):
    text = '출구 구역 독립 유량 분할: 사용자가 보완한 해결안과 인용 근거를 모두 검토한다.\n' * 3500
    context = {'source': {'text': text}, 'answers': {'Q03': '새로운 답변'},
               'review_targets': [{'target_id': 'section-1', 'target_hash': digest(text)}]}
    schema = {'type': 'object', 'description': '전체 기술 자료를 검토한 결과'}
    requests = []
    def respond(request):
        body = json.loads(request.content); requests.append(body)
        assert json.loads(body['messages'][1]['content']) == context
        assert canonical(schema) in body['messages'][0]['content']
        return httpx.Response(200, json={'model': name, 'usage': {'prompt_tokens': 12345, 'completion_tokens': 50},
            'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}]})
    result = Gateway(httpx.MockTransport(respond)).generate(model(name), '검토 지시', context, schema)
    measured = result['boundary_contract']['input_measurement']
    assert measured['content_bytes'] > 262144 > measured['admission_tokens']
    assert measured['content_tokens'] < measured['admission_tokens']
    assert result['boundary_contract']['data_hash'] == digest(context)
    assert result['cost_micro_usd'] == model(name).cost(12345, 50)
    assert len(requests) == 1


def test_true_token_overflow_is_not_sent_or_truncated():
    requests = []
    gateway = Gateway(httpx.MockTransport(lambda request: requests.append(request)))
    with pytest.raises(PatentError) as error:
        gateway.generate(model(limit=2048), 'review', {'source': '유량 분할 기술 자료\n' * 10000}, {})
    assert error.value.code == 'REVIEW_COVERAGE_LIMIT'
    assert requests == []


def test_instruction_and_schema_are_included_in_admission():
    gateway = Gateway(httpx.MockTransport(lambda request: pytest.fail('must not call provider')))
    for instruction, schema in [('모든 항목 검토 ' * 4000, {}), ('review', {'description': '모든 항목 검토 ' * 4000})]:
        with pytest.raises(PatentError) as error:
            gateway.generate(model(limit=2048), instruction, {}, schema)
        assert error.value.code == 'REVIEW_COVERAGE_LIMIT'


def test_unknown_model_uses_bound_and_missing_tokenizer_stops_before_billing(monkeypatch):
    measured = input_tokens.measure(model('unrecognized-model'), [{'content': '한글'}])
    assert measured['content_tokens'] == len('한글'.encode())
    def missing(): raise FileNotFoundError()
    monkeypatch.setattr(input_tokens, 'tokenizers', missing)
    with pytest.raises(PatentError) as error:
        Gateway(httpx.MockTransport(lambda request: pytest.fail('must not call provider'))).generate(model(), '', {}, {})
    assert error.value.code == 'INPUT_TOKENIZER_UNAVAILABLE'


def test_bundled_tokenizers_never_truncate_and_detect_corrupt_assets(tmp_path, monkeypatch):
    assert all(t.truncation is None and t.padding is None for t in input_tokens.tokenizers())
    monkeypatch.setattr(input_tokens, 'ROOT', tmp_path)
    (tmp_path / 'v4').mkdir()
    (tmp_path / 'v4/tokenizer.json').write_text('{}')
    (tmp_path / 'manifest.json').write_text(json.dumps({'files': {'v4/tokenizer.json': 'incorrect'}}))
    with pytest.raises(ValueError, match='checksum'):
        input_tokens.tokenizers.__wrapped__()
