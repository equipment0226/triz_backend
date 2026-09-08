# TRIZ Studio Backend

FastAPI + TRIZ MCP 52 tools + n8n queue + MySQL.

Frontend: https://github.com/equipment0226/triz_front

## Railway

이 저장소 루트의 Dockerfile과 railway.json을 사용한다. API와 MCP는 동일 서비스·볼륨에서 실행한다.
MCP endpoint는 `/agent/mcp`, n8n bridge는 `/internal/execute`다.
`/healthz`는 DB readiness 검사이며 유료 모델을 호출하지 않는다.

- [단계별 배포](deploy/RAILWAY.md)
- [설계서](docs/TRIZ_MASTER_SPEC.md)
- [피드백 반영표](docs/FEEDBACK_IMPLEMENTATION.md)

## Local

```sh
python -m pip install -r pilot/requirements.txt
cp pilot/.env.example pilot/.env
python pilot/run.py
```

프런트엔드는 별도 저장소에서 실행한다. Git에 실제 키·입력 데이터·보고서를 저장하지 않는다.

```sh
python -m pip install pytest
python -m pytest pilot/tests -q
python pilot/scripts/smoke.py
```
