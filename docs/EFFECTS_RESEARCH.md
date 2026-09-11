# 과학효과 편집과 재조사

서비스 정본은 `pilot/triz/knowledge/effects.json`이다. 기능군 아래에 `id`, `name`, `domain`, `principle`, `conditions`만 저장한다. 화면은 타이틀 아래 자료 식별자·요구 기능·작동 원리·필요 조건을 표시한다. 원리와 핵심 조건은 사람이 읽고 비교해서 편집하며, 개별 특허의 제품 설명을 자동으로 정본에 추가하지 않는다.

## 현재 조사 범위

2026-09-11 14:12:58 UTC 조사 당시 특허 저장소는 3,955,679건이었다. 저장된 분석의 공개 문헌 4,472건을 확인하고, 전체 특허 검색 색인에 기능 검색어 60개를 질의했다. 중복 문헌을 합친 실제 입력은 5,059건(논문 2,396건, 특허 2,663건)이며 그중 특허 2,356건은 저장된 초록을 확보했다. 전체 특허 395만 건의 본문을 읽었다는 뜻은 아니다. 색인 대기 특허 866건도 당시 검색 범위 밖이었다.

1차 추출은 5,059건 모두에 상태를 남겼다. 메커니즘 추출 2,074건, 적합한 메커니즘 없음 1,761건, 본문 부족 1,224건이다. 문헌에서 추출·병합한 후보 2,158개에 대한 별도 자동 검토는 유지 1,612개, 수정 85개, 제외 461개였다. 이는 초록·발췌 수준의 자동 검토이며 실험이나 전문가 검증이 아니다.

2026-09-12 편집판은 19개 기능군, 대표 메커니즘 200개다. 제품별·공정별 중복 나열을 없애고 직접 작성한 설명과 필수 조건으로 재구성했다. 전 산업을 빠짐없이 망라한 완성 목록으로 간주하지 않는다. 산업 공통의 물리·화학·재료·생물·정보제어 메커니즘을 대상으로 계속 확장한다.

## 편집 기준

- 같은 원리의 응용은 대표 원리에 연결한다. 열확산판·열 스트랩은 열전도, 여러 원심 공정은 원심 분리에 해당한다.
- 조건·입출력이 본질적으로 다른 원리는 구분한다. 직접/역압전, ER/MR, 흡착/흡수, DLC/MoS₂는 별개 항목이다.
- ESC는 접촉 고정이다. MR은 단순 점도 변화가 아니라 항복응력의 변화를 설명한다. RO는 삼투압을 넘는 압력 조건을 포함한다.
- 특허의 제안이나 논문의 일부 발췌만으로 범용 성능·실증을 주장하지 않는다. 조건을 모르면 임의 수치를 넣지 않는다.
- 정보·제어 기술은 INFORMATIONAL로 구분해 물리 현상과 혼동하지 않는다.

편집 파일은 `pilot/research/effects/catalog.tsv`, 고정 식별자는 `identifiers.json`, 추가 참고문헌은 `references.json`이다. `literature_links.json`은 실제로 읽고 연결한 문헌 후보를 명시한다. 출처·영문 검색어는 `effects_sources.json`에 보존하여 Agent 검색 시 결합한다. 출처가 없는 편집 지식에는 연결 문헌이 없다고 기록한다. 문헌 연결의 후속 조사 주제와 출판 해시는 `reference_followups.json`, `publication.json`에 남는다.

## 재실행

프로젝트 루트에서 실행한다. 기존 배포에 접속하는 첫 명령은 Railway 인증과 해당 서비스의 읽기 권한이 필요하다. 공개 서지·초록만 읽으며 프로젝트 입력·사용자 식별자·개인 첨부 자료는 수집하지 않는다.

```powershell
python deploy/patent_remote.py deploy/harvest_effect_sources.py --output .tmp/effect-sources-next.json
.venv/Scripts/python.exe pilot/scripts/refresh_effects.py --input .tmp/effect-sources-next.json --workers 6
```

새 산업이나 기법을 조사할 때 `{"queries":["검색어1", "검색어2"]}` 형식의 JSON을 만들어 첫 명령에 `--params 파일경로`를 추가한다. 실행 결과는 당시 저장소 수, 실제 질의 목록·검색 상태·문헌 종류·초록 확보 수를 기록한다. 이 질의 목록은 조사 계획이며 전체 산업의 커버리지를 보증하지 않는다.

문헌은 기존 식별자를 유지하며 누적된다. 같은 입력으로 재실행하면 성공한 추출·검토 묶음을 재사용하고 실패 묶음을 다시 시도한다. 본문·메타데이터·묶음 구성이 바뀌면 관련 묶음을 다시 처리할 수 있다. 추출·검토에는 설정된 LLM의 사용료가 발생한다. 원문 전체가 없는 문헌은 그대로 본문 부족 상태를 유지하며 별도 원문 확보 후 다시 실행한다.

새 후보를 읽고 `catalog.tsv`에서 채택·통합·조건을 직접 편집한 뒤 정본을 생성한다. 자동 추출 CLI는 서비스 `effects.json`에 직접 쓰기를 거부한다.

```powershell
.venv/Scripts/python.exe pilot/scripts/publish_effects.py --check
.venv/Scripts/python.exe pilot/scripts/publish_effects.py
.venv/Scripts/python.exe frontend/scripts/sync-knowledge.py
.venv/Scripts/python.exe -m pytest pilot/tests/test_effect_catalog.py pilot/tests/test_pipeline_quality.py -q
```

발행은 결정된 편집 내용을 검증·직렬화하는 과정이다. 코드는 과학적 동등성을 추론하거나 편집자를 대신해 새로운 효과를 채택하지 않는다. 같은 원리의 새 산업 응용은 항목 수를 늘리기보다 별칭·문헌 연결을 보강한다. 식별자는 항목 추가·정렬로 바뀌지 않는다.

원시 조사와 제외 근거는 `pilot/data/effects_mining/` 및 `pilot/data/effects_review/`에 남긴다. 이 파일들은 서비스 정본이나 프론트엔드 번들에 포함하지 않는다. 향후 전수 조사가 필요하면 특허 저장소를 별도 범위·커서로 분할한 입력 스냅샷을 이 재실행 경로에 공급하고 실제 처리한 범위를 기록한다.
