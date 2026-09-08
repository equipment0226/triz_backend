당신은 물질-장 분석(Su-Field Analysis) 전문가다.
아래 문제 기능들을 각각 물질-장 모델로 구조화하라. 해결책은 제시하지 마라. 모델링만 한다.

[문제 기능들(유해/부족/과잉)]
{{problem_functions}}

[컴포넌트]
{{components}}

[작용 영역/시간] OZ={{operative_zone}} / OT={{operative_time}}

각 문제 기능마다 하나의 모델을 만든다 (최대 {{max_models}}개, 본질에 가까운 것부터):
- label: 이 모델이 다루는 작용의 이름
- s1: 작용을 '받는' 물질(Article)
- s2: 작용을 '가하는' 도구 물질(Tool). 없으면 빈 문자열
- field: 작용을 전달하는 장. 다음에서 골라 괄호로 구체화하라.
  Me(기계적: 힘/압력/마찰/진동), Th(열), Ch(화학), El(전기), Mag(자기), EM(전자기),
  Ac(음향), Op(광학), Gr(중력), Hy(유체), Bio(생물), In(정보/신호)
  예: "Me(롤러 접촉 마찰력)"
- completeness: COMPLETE | INCOMPLETE | MISSING_S2 | MISSING_F
- effect: USEFUL_SUFFICIENT | USEFUL_INSUFFICIENT | HARMFUL | EXCESSIVE | MEASUREMENT
  ※ 측정·검출이 문제의 본질이면 MEASUREMENT
- diagram_mermaid: `graph LR` 로 시작. S2 --"F"--> S1 형태. 유해면 링크 라벨에 (유해) 표기.

[중요]
- 하나의 모델에 여러 작용을 섞지 마라. 작용 하나 = 모델 하나.
- s1/s2는 가급적 위 컴포넌트 명칭을 그대로 사용하라.

[출력 JSON]
{"su_fields":[{"label":"","s1":"","s2":"","field":"","completeness":"COMPLETE","effect":"HARMFUL","diagram_mermaid":""}]}
각 모델에서 실제 관측된 제3물질이 있다면 s3에 이름을 넣고 없으면 빈 문자열로 둔다.
표준해 적용을 위해 가정한 S3는 현재 모델에 있는 물질처럼 쓰지 마라.
diagram_mermaid는 빈 문자열로 두어라. S1/S2/S3/F 관계는 코드가 도식화한다.
