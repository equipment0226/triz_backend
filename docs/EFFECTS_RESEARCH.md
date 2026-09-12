# 과학효과 편집과 재조사

서비스 정본은 `pilot/triz/knowledge/effects.json`이다. 기능군 아래 `id`, `name`, `domain`, `principle`, `conditions`만 저장한다. 화면은 타이틀·자료 식별자·요구 기능·작동 원리·필요 조건을 표시한다. 출처·별칭은 `effects_sources.json`에서 Agent 검색에 결합한다.

## 현재 방식과 범위

사용자 요청에 따라 2026-09-12부터 **이 대화의 직접 추론**으로 조사한다. 외부 LLM API로 추출·재검토하지 않는다. `research_policy.json`의 `external_llm_calls_allowed: false`가 오프라인 `mine`·`review_catalog`의 기본 모델 호출을 차단한다. 이 정책은 서비스 이용자의 대화형 TRIZ 분석과 별개다. 서버 과학효과 워커 이전은 취소된 상태이며 자동 실행 서비스를 만들지 않았다.

대상은 DB에 적재되는 **전체 산업의 전체 특허**다. IT·통신·소프트웨어·보안·정보처리도 포함하며 업종 필터를 걸지 않는다. `effect_source_pages.harvest_page`는 검색 상위 결과가 아닌 공개번호 순서로 저장 초록을 읽는다. 2026-09-12 01:58:49 UTC 조회 당시 저장소는 4,810,073건이었다. 계속 적재 중이므로 고정 총량이 아니다.

이번 직접 검토는 AP-00143-S1부터 AR-026778-A1까지 조회한 1,200건이다. 초록 782건을 직접 읽어 원리 연결 334건, 추가 확인 보류 248건, 설계 구성 198건, 근거 부족 주장 제외 2건으로 기록했다. 나머지 418건은 초록 없음이며 읽거나 분석한 초록 수에 넣지 않는다. DB에서 확보한 것은 서지와 초록이며 청구항·명세서·도면 전문은 아니다. 전체 수백만 건을 읽었다는 뜻이 아니며 전체 순회는 미완료다.

현재 정본은 **19개 기능군, 269개 효과**다. 217개에서 52개를 직접 편집해 추가했다. IT의 OFDM·시분할 다중화·분산 장벽 동기화·지도 학습·상관 검출·변환 영역 합성곱·힐베르트 변환·최단 경로 탐색도 포함한다. 246개는 참고 문헌이 연결되고 23개는 연결 문헌 없는 편집 지식이다. 네 번째 검토에서는 기존 원리에 특허 근거를 추가했으며, 신규 메커니즘 후보는 교차 확인 전까지 정본에 넣지 않았다. 참고 문헌 연결이 모든 현장 조건·성능의 실증을 뜻하지 않는다.

## 편집 원칙

- 원리·입력·출력·필요조건을 직접 비교한다. 제품명·산업·특허번호가 달라도 같은 원리면 기존 항목에 연결한다.
- 물리·화학·기하·생물·정보 원리를 구분한다. 소프트웨어를 억지로 물리 효과에 대응시키지 않는다.
- 단순 서비스 흐름·UI·제품 조합만으로 새 원리를 만들지 않는다. IT 알고리즘도 실제 처리 과정과 성립 조건이 있어야 한다.
- 특허의 제안·효능 주장을 실험 결과나 보편적 성능으로 취급하지 않는다. 초록에 없는 수식·수치·표적을 출처에 귀속하지 않는다.
- 부분 초록·번역 오류·깨진 수식은 보류 이유로 남긴다. 다형과 결정 외형, 압저항과 접점 닫힘, 피커링 유화와 전분 배합 등을 구분한다.
- 정본은 간결하게 유지한다. 상세 판단·출처·검색 별칭은 별도 파일에 남긴다.

`catalog.tsv`가 직접 편집한 정본이고 `identifiers.json`이 변경하지 않는 식별자 원장이다. `references.json`에는 공식·일차 문헌, `editorial_metadata.json`에는 직접 편집한 분야·별칭을 둔다. `literature_links.json`과 `accepted_literature_sources.json`은 실제 읽은 문헌과 원리를 연결한다. `review-2026-09-12-manual.md`와 `manual-patents-2026-09-12.tsv`(191건), `manual-patents-2026-09-12-02.tsv`(195건), `manual-patents-2026-09-12-03.tsv`(200건), `manual-patents-2026-09-12-04.tsv`(196건)에 이번 판단을 기록했다.

## API 없이 이어서 조사하기

원시 페이지는 `pilot/data/patent_effects_manual/page-000001.json`부터 저장돼 있다. 요약은 `pilot/research/effects/manual-progress.json`, 1,200건 상태 원장은 `pilot/data/patent_effects_manual/review-ledger.json`이다. `manual_reviews/`의 01·02·03·04 검토 기록은 각 결정을 입력 내용 해시에 결합한다. 바뀐 초록에 이전 결정을 자동 적용하지 않는다.

여섯 페이지는 `manual_archives/2026-09-12-04.json.gz`에도 보존했다. 이전 01·02·03 압축본은 처음 세·네·다섯 페이지의 기록으로 유지한다. 각 압축본의 내용은 공개 서지·초록 페이지 JSON의 배열이며 서로 중복되므로 합산하지 않는다. 원시 페이지가 없으면 최신 04 압축본에서 각각 `page-000001.json`부터 복원할 수 있다. 사용자 프로젝트·개인 첨부·인증정보는 포함하지 않는다.

먼저 기존 기록의 상태를 계산한다. API나 추론을 호출하지 않는다.

```powershell
.venv/Scripts/python.exe pilot/scripts/record_manual_effect_reviews.py
```

미검토 초록이 0건일 때 다음 묶음을 조회한다. 위 명령이 다음 요청 파일을 생성한다. 현재 커서는 `AR-026778-A1`, 이번 순회의 상한은 `ZA-F202500713-S`다. 기존 파일을 덮어쓰지 않고 다음 번호로 저장한다. 서버 접속은 기존 Railway 인증을 사용하며 DB는 읽기만 한다.

```powershell
.venv/Scripts/python.exe deploy/patent_remote.py deploy/harvest_manual_patent_page.py --params pilot/data/patent_effects_manual/next-request.json --output pilot/data/patent_effects_manual/page-000007.json
```

새 초록을 대화에서 직접 읽고 별도 TSV에 `공개번호|LINK 또는 DEFER 또는 DESIGN_ONLY 또는 REJECT_CLAIM|정본 키,정본 키|판단 이유`를 작성한다. LINK는 이미 편집한 `catalog.tsv` 키만 참조한다. 초록 없는 행은 정확한 빈 문자열 여부로 표시하며 직접 읽은 것으로 등록하지 않는다.

```powershell
.venv/Scripts/python.exe pilot/scripts/record_manual_effect_reviews.py --record pilot/research/effects/manual-next.tsv --review-id next-review --link-sources
.venv/Scripts/python.exe pilot/scripts/publish_effects.py --check
.venv/Scripts/python.exe pilot/scripts/publish_effects.py
.venv/Scripts/python.exe frontend/scripts/sync-knowledge.py
.venv/Scripts/python.exe -m pytest pilot/tests/test_manual_effect_reviews.py pilot/tests/test_effect_catalog.py pilot/tests/test_pipeline_quality.py pilot/tests/test_standard_diagrams.py -q
```

발행·원장 코드는 작성된 결정을 검증·직렬화한다. 과학적 동등성 판단·요약·채택을 코드가 대신하지 않는다. 검토 JSON은 불변이며 수정에는 새 review-id가 필요하다. 미검토 초록이 있으면 완료 커서는 그 페이지 앞에서 멈춘다. 다음 페이지를 조회하기 전에 해당 부분부터 읽는다.

이 순회는 엄밀한 DB 시점 스냅샷이 아니다. 이미 지나간 공개번호 위치의 신규 특허·변경 초록은 다음 순회에서 확인한다. 순회를 끝낸 뒤 새 페이지 폴더에서 커서·상한을 비워 시작하고 이전 검토 해시와 대조한다. 본문 없는 자료는 원문 확보 전까지 자료 부족으로 유지한다.

## 이전 자동 조사 기록

정책 변경 전 공개 문헌 5,059건(논문 2,396·특허 2,663)을 자동 처리했다. 추출 2,074건, 기구 없음 1,761건, 본문 부족 1,224건이며 후보 2,158개의 자동 검토는 유지 1,612·수정 85·제외 461개였다. 직접 읽거나 정본에 채택한 수가 아니다. 원시 결과는 `pilot/data/effects_mining/`, `pilot/data/effects_review/`에 남아 있다.

이전 API 순차 조사도 600건(초록 223·빈 초록 377)과 부분 완료 다음 묶음을 남겼다. `pilot/data/patent_effects_sweep/`에 중지 상태로 보존한다. 새 직접 검토 구간과 중복되므로 합산하지 않는다. 재조회 때 과거 커서 앞에도 새 특허가 들어온 사실을 확인했다. `refresh_effects.py`, `sweep_patent_effects.py`, `effect_worker.py`는 현재 과학효과 조사에 실행하지 않는다.
