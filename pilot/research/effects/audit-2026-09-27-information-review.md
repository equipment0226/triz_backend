# 정보·통계·계산 효과 검토 — 2026-09-27

상태: 진행 중. 시작 정본 1,500개 중 정보군은 205개이다. 정본·식별자·출처 레지스트리는 수정하지 않았다. 대화의 직접 추론으로 기존 키와 원리·조건을 대조하고 공개 원문 및 공식 문서를 조회했다. 외부 LLM API 호출은 0회이다.

판정 기준은 상위 개념에 속한다는 사실이 아니라 입력, 실제 변환, 성립 조건의 동일성이다. PLL과 음의 피드백처럼 구체적인 동역학과 설계 조건이 다른 항목은 유지한다. 소재·응용·참조 축만 바뀐 경우는 병합 후보로 기록한다. 형식 검사가 전체 쌍의 의미론적 독립성을 증명하지는 않는다.

## 기존 항목 감사

- 병합 권고: `cross-channel-predictive-coding`, `spatial-intra-prediction`, `autoregressive-linear-prediction`. 세 항목은 참조값에서 예측을 만들고 잔차를 표현한다. 채널·영상 공간·과거 시간의 참조 축 차이이다. 대표 `autoregressive-linear-prediction`의 제목·원리·조건을 일반적인 상관 기반 예측·잔차 부호화로 넓힌 뒤 3→1로 통합할 수 있다. 모든 ID·이름·문헌 이관이 필요하다.
- 추가 검토: `quadrature-carrier-channel-separation`과 `lock-in-detection`. 두 직교 기준에 동기 곱셈·누적을 반복하는 구조이지만, 직교성에 의한 채널 분리 조건을 대표에 충분히 보존하는지 판단한 뒤 처리한다. 자동 병합하지 않는다.
- 유지: PLL/일반 피드백/동기 검파, 일반 상태 추정/입자 가중·재표본화, 고전/양자 오류 정정, 결측 행렬 복원/완전 행렬의 특이값 절단, 기준 센서 차분/알려진 기대값의 제어변량 보정. 구체적인 변환 또는 참조 입력 조건이 다르다.

각 후보의 기존 원문 행과 근거는 같은 이름의 JSON에 저장했다.

## 신규 배치

`additions-2026-09-27-information-01.tsv`: 수치해석·최적화·논리·대수의 신규 연산 20개. 행마다 10열, 원리 160자 이하, 조건 180자 이하, HTTPS 출처, 실제 존재하는 최근접 키를 검사했다. 키 충돌 없음.

출처의 관련 식·알고리즘을 직접 확인한 경우 `reference_section`으로 기록했다. Nelson–Oppen 합동 폐쇄 논문은 직접 PDF 열기 오류가 있어 검색에 보존된 원문 §2 발췌만 확인한 `stored_search_excerpt`이다. 각 출처에서 확인한 내용과 URL은 JSON의 `new_source_records`에 남겼다.

동일 쌍대 연산의 열 생성/절단 평면, 운동량 계수별 변형, 기존 오차 외삽·제어변량의 재조합, 기존 오류 정정·필터·추론 알고리즘의 응용별 변형은 별도 신규 수로 세지 않았다.

Batch 02: 15 statistical mechanisms. Total authored: 35. Schema, lengths, HTTPS, scopes, unique new keys, and related-key existence checked. Already installed batch-01 rows were compared for exact agreement. JSON source observations repaired after detecting damaged console encoding. Camera triangulation excluded because bearing-ray-triangulation already exists.

Batch 03: 18 image, signal, learning, PDE and numerical mechanisms. Total authored: 53. Schema and nearest-key checks passed. K-means excluded due to explicit EM equivalence in official documentation.

Batch 04: 20 distributed-computing, memory, scheduling and cryptographic mechanisms. Total authored: 73. Schema and nearest-key checks passed. Only own audit-review files updated; installer-owned audit-additions files untouched.

Batch 04 correction before installation: removed underspecified oblivious-transfer card after parent review; garbled-circuit related keys updated. Batch 04 now 19, cumulative 72. Candidate evidence and exclusion recorded in JSON.

Batch 05: 20 graph, symbolic algebra, approximation, numerical integration, coding and sampling operations. Total authored: 92. Schema, lengths, existing/new related keys, and installed-row agreement passed. No canonical registry changes by this agent.

Batch information-06: 16 mechanisms; cumulative authored count 108. All sources retrieved at reference-section scope. Three stochastic-gradient families have different required operations: score weighting, differentiable base-noise transport, and signed-measure decomposition. SURE risk estimation does not duplicate James-Stein shrinkage. Attention and bilateral variants were not separately counted beside content-similarity normalized aggregation. MC-SURE and UCB coefficient variants were excluded as combinations/variants. Gaussian-risk original Yale scan and EPFL preprint retrieval failed; accessible NeurIPS 2018 primary research section 2.1 supplies the explicit identity instead.

Batch information-07: 20 mechanisms; cumulative authored count 128. Nineteen reference-section records and one honestly stored publisher search excerpt (internal-model principle, publisher 403). Controls are retained for explicit cancellation, flat-output reconstruction, supply-rate cancellation, exosystem embedding, and nilpotency conditions rather than treated as duplicate generic feedback. Feynman-Kac card explicitly restricts the expectation representation to linear PDEs and records its inference from primary BSDE equations. Computational geometry was handed to root. Counts do not include balanced truncation, fast marching, Nyquist criterion or application variants.


Batch 08: 16 new operations; cumulative 144. Delay embedding, transfer entropy, cumulants, Magnus propagation, Carleman lift, costate control, describing functions, proper outcome scores, dependent rounding, finite-field factorization, meet-in-the-middle powers, factorial contrasts, correlation dimension, infeasibility witnesses, spectral disks and wave-variable delay passivation were compared with the current catalog. All 16 use reference-section scope; auxiliary Mendel support is explicitly only an indexed excerpt. No canonical files were edited.

Batch 09: 15 new operations; cumulative authored count 159. All reference-section evidence. CDF supremum, distance-matrix dependence, spectral random features, sign-invariant real cells, polynomial primality checks, three distinct factor-discovery paths, uniformized Markov propagation, inequality elimination, integer invariant factors, integer cuts, Ito correction, variance stabilization and empirical likelihood were checked against the current 1822-row canonical catalog. Algebraic primitives used inside more complex operations are distinguished from actual duplicate mechanisms. No central files were changed.

Batch 10: 9 completed mathematical operations; cumulative authored count 168. Matched expansions, multiple-time secular removal, injective neighbor-color refinement, row-hyperplane projection, complementary-label pivots, coordinate-replacement variance bound, functional variance decomposition, modular-root correction and feasible-basis exchange all have reference-section evidence. Saved the completed subset before a parent-requested read-only patent-search fairness audit. Other candidates remain uncounted. No canonical files changed.

Batch 10 hold: parent requested implementation of a separate balanced manual patent-review queue before further effect research. The nine saved rows remain authored candidates awaiting parent integration; no new science effects or central research files are being changed during this bounded implementation task.
