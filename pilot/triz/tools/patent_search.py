"""Request pacing and outage detection for the existing patent provider."""
import threading
import time
import re
import httpx
from ..settings import settings

_lock = threading.Lock()
_cooldown = {}
_last_request = {}


class Unavailable(Exception):
    def __init__(self, provider, reason, status=None, retry_after=None):
        self.detail = {'provider': provider, 'reason': reason, 'http_status': status,
                       'retry_after': retry_after}
        super().__init__(reason)


def request(provider, method, url, **kwargs):
    # Share pacing across concurrent runs in this worker. No proxy or provider switch.
    with _lock:
        blocked = _cooldown.get(provider, {})
        if blocked.get('until', 0) > time.time():
            raise Unavailable(provider, 'COOLDOWN', blocked.get('status'), blocked['until'])
        interval = float(settings.cfg('evidence.patent_request_interval_seconds', 1))
        wait = interval - (time.monotonic() - _last_request.get(provider, 0))
        if wait > 0:
            time.sleep(wait)
        _last_request[provider] = time.monotonic()
        try:
            response = getattr(httpx, method)(url, **kwargs)
            response.raise_for_status()
            if re.search(r'<title>\s*(?:Sorry\.\.\.|Just a moment\.\.\.)\s*</title>', response.text, re.I):
                retry_after = time.time() + 300
                _cooldown[provider] = {'until': retry_after, 'status': response.status_code}
                raise Unavailable(provider, 'ACCESS_CHALLENGE', response.status_code, retry_after)
            return response
        except httpx.HTTPError as exc:
            code = exc.response.status_code if isinstance(exc, httpx.HTTPStatusError) else None
            retry_after = None
            if code in (401, 403, 429, 503) or code is None or code >= 500:
                delay = 300
                if isinstance(exc, httpx.HTTPStatusError):
                    raw = exc.response.headers.get('Retry-After', '')
                    if raw.isdigit(): delay = max(delay, int(raw))
                retry_after = time.time() + delay
                _cooldown[provider] = {'until': retry_after, 'status': code}
            raise Unavailable(provider, 'HTTP_ERROR' if code else 'NETWORK_ERROR', code, retry_after) from None
