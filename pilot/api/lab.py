"""Manual n8n tests: native MCP stages, client-carried state, no run DB."""
import secrets
from typing import Literal

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from triz import lab_transport
from triz.settings import settings


def service_auth(authorization: str = Header(default='')):
    if not settings.service_token or not secrets.compare_digest(authorization, 'Bearer ' + settings.service_token):
        raise HTTPException(401, 'Unauthorized')


router = APIRouter(prefix='/internal/lab', dependencies=[Depends(service_auth)])


class BeginBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    raw_query: str = Field(default='', max_length=100000)
    mode: Literal['QUICK', 'STANDARD', 'DEEP'] = 'STANDARD'
    budget_usd: float = Field(default=5, gt=0, le=5)
    continuation: str = Field(default='', max_length=lab_transport.MAX_TOKEN_BYTES)
    human_response: dict | None = None


class StageBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    continuation: str = Field(min_length=1, max_length=lab_transport.MAX_TOKEN_BYTES)
    stage_key: str = Field(min_length=1, max_length=48)
    human_response: dict | None = None


class InspectBody(BaseModel):
    model_config = ConfigDict(extra='forbid')
    continuation: str = Field(min_length=1, max_length=lab_transport.MAX_TOKEN_BYTES)
    candidate_id: str = Field(default='', max_length=100)


@router.get('/manifest')
def manifest():
    from triz.lab_manifest import build_manifest
    return build_manifest()


async def call_mcp(payload):
    from triz.mcp_client import execute_lab
    try:
        lab_transport.validate_payload(payload)
        return await execute_lab(payload)
    except lab_transport.LabInputError as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        # A transport error can follow a paid request. Never replay it here.
        raise HTTPException(502, '테스트 API 응답을 확인하지 못했습니다. 자동 재호출하지 않았습니다.') from exc


@router.post('/begin')
async def begin(body: BeginBody):
    return await call_mcp(dict(body.model_dump(), action='begin'))


@router.post('/stage')
async def stage(body: StageBody):
    return await call_mcp(dict(body.model_dump(), action='stage'))


@router.post('/inspect')
def inspect(body: InspectBody):
    try:
        return lab_transport.inspect_solutions(body.continuation, body.candidate_id)
    except lab_transport.LabInputError as exc:
        raise HTTPException(422, str(exc)) from exc
