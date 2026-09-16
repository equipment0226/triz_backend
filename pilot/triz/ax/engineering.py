"""Allowlisted calculations. A model calculation is never a physical test result."""
import math
from .contracts import digest


def dlc_steady_state(inputs):
    required={'inlet_c','heat_w','total_resistance_k_per_w','gpu_limit_c'}
    missing=sorted(required-set(inputs))
    if missing: return {'status':'NOT_RUN','missing':missing,'scope':'steady_state_calculation'}
    x={k:float(inputs[k]) for k in required}
    if not all(math.isfinite(v) for v in x.values()) or x['heat_w']<0 or x['total_resistance_k_per_w']<=0:
        return {'status':'ERROR','reason':'Finite values and positive thermal resistance required'}
    estimated=x['inlet_c']+x['heat_w']*x['total_resistance_k_per_w']
    return {'status':'PASS' if estimated<=x['gpu_limit_c'] else 'FAIL',
        'estimated_gpu_c':estimated,'margin_k':x['gpu_limit_c']-estimated,
        'input_hash':digest(inputs),'scope':'steady_state_calculation',
        'assumptions':['총 열저항에 계면·콜드플레이트·유체 측 저항이 포함됨','정상 상태와 동일 열부하',
                       '펌프 동력·압력손실·결로·재료 호환성은 이 계산의 검증 범위 밖'],
        'physical_test_performed':False}


TOOLS={'dlc_steady_state_v1':dlc_steady_state}


def run(tool,inputs):
    if tool not in TOOLS: raise ValueError('Calculation tool not registered')
    return TOOLS[tool](inputs)
