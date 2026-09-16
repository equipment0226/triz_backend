"""DrawingSpec rendering plus the user-selected movable CPU diffusion adapter."""
from html import escape
import os
from urllib.parse import urlparse
import httpx
from .domain import DrawingSpec, PatentError
from triz.display_terms import display_text

SAMPLE_IMAGE_NOTICE = '해당 이미지는 생성형 AI를 활용한 샘플 이미지입니다.'
MAX_GENERATED_IMAGES_PER_CASE = 1


def svg(spec):
    spec = DrawingSpec.model_validate(spec)
    outputs = {}
    for drawing in spec.drawings:
        positions = {node['id']: (40+(i%3)*210, 70+(i//3)*100) for i, node in enumerate(drawing.nodes)}
        if len(positions) != len(drawing.nodes):
            raise PatentError('DRAWING_REFERENCE', '도면 부호가 중복됩니다.', 422)
        width, height = 680, 100+((len(drawing.nodes)+2)//3)*100
        parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
                 '<rect width="100%" height="100%" fill="white"/>',
                 f'<text x="20" y="30" fill="black">도 {drawing.number} — {escape(display_text(drawing.caption))}</text>']
        for edge in drawing.edges:
            if edge.get('from') not in positions or edge.get('to') not in positions:
                raise PatentError('DRAWING_REFERENCE', '도면 연결에 없는 부호가 있습니다.', 422)
            a, b = positions[edge['from']], positions[edge['to']]
            parts.append(f'<line x1="{a[0]+80}" y1="{a[1]+30}" x2="{b[0]+80}" y2="{b[1]+30}" stroke="black"/>')
        for node in drawing.nodes:
            x, y = positions[node['id']]
            parts += [f'<rect x="{x}" y="{y}" width="170" height="60" fill="white" stroke="black"/>',
                      f'<text x="{x+8}" y="{y+35}" fill="black">{escape(node["id"]+" "+display_text(node.get("label", "")))}</text>']
        outputs[f'figure-{drawing.number}.svg'] = ''.join(parts+['</svg>']).encode()
    return outputs


class DiffusionAdapter:
    def __init__(self, transport=None):
        self.base = os.getenv('PATENT_DRAWING_URL', '').rstrip('/')
        self.token = os.getenv('PATENT_DRAWING_TOKEN', '')
        self.transport = transport

    def request(self, method, path, **kwargs):
        parsed = urlparse(self.base)
        allowed = set(os.getenv('PATENT_DRAWING_ALLOWED_HOSTS', '').split(','))
        private = parsed.scheme == 'http' and (parsed.hostname or '').endswith('.railway.internal')
        if not self.token or not parsed.hostname or parsed.hostname not in allowed or not (parsed.scheme == 'https' or private):
            raise PatentError('DRAWING_UNAVAILABLE', '도면 생성 서버 연결을 설정해야 합니다.', 503)
        try:
            with httpx.Client(transport=self.transport, timeout=30, follow_redirects=False) as c:
                r = c.request(method, self.base+path, headers={'Authorization': 'Bearer '+self.token, **kwargs.pop('headers', {})}, **kwargs)
            if r.status_code not in (200, 202):
                raise ValueError('drawing response')
            return r
        except Exception:
            raise PatentError('DRAWING_UNAVAILABLE', '도면 서버의 응답을 확인할 수 없습니다.', 503, True) from None

    def create(self, case_id, version_id, prompt, key):
        return self.request('POST', '/v1/drawings', headers={'Idempotency-Key': key}, json={
            'case_id': case_id, 'artifact_version_id': version_id, 'prompt': prompt,
            'seed': 42, 'steps': 20, 'width': 512, 'height': 512}).json()

    def status(self, job_id):
        if len(job_id) != 32 or any(c not in '0123456789abcdef' for c in job_id):
            raise PatentError('DRAWING_ID', '도면 작업 ID가 잘못됐습니다.', 422)
        return self.request('GET', '/v1/drawings/'+job_id).json()

    def image(self, job_id):
        self.status(job_id)  # Validates the opaque identifier and service ownership.
        response = self.request('GET', '/v1/drawings/'+job_id+'/image')
        value = response.content
        if len(value) > 4_000_000 or not value.startswith(b'\x89PNG\r\n\x1a\n'):
            raise PatentError('DRAWING_RESPONSE_INVALID', '도면 이미지 응답이 잘못됐습니다.', 503)
        return value
