import os
import sys
import tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Never touch the user's PoC database or call a real model in regression tests.
TEST_DIR = tempfile.TemporaryDirectory(prefix="triz-tests-")
os.environ["DATABASE_URL"] = "sqlite:///" + (Path(TEST_DIR.name) / "test.db").as_posix()
os.environ["STORAGE_DIR"] = str(Path(TEST_DIR.name) / "storage")
os.environ["ORCHESTRATOR"] = "local"
os.environ['TRIZ_AX_ENABLED']='false'  # Legacy regression fixtures; AX tests opt in explicitly.
os.environ["LLM_API_KEY"] = "offline-test"
os.environ["TRIZ_SERVICE_TOKEN"] = "offline-test-service"
import pytest
@pytest.fixture(autouse=True)
def no_paid_calls(monkeypatch):
    from triz import llm
    from triz.settings import settings
    # Existing regression fixtures characterize persisted contracts. New-run
    # acceptance fixtures explicitly select ax-run-v2 after this fixture.
    monkeypatch.setitem(settings.triz['ax'], 'run_contract_version', 'legacy')
    monkeypatch.setattr(llm, "chat_json", lambda **kwargs: (_ for _ in ()).throw(AssertionError("Unexpected real LLM call")))
    import socket
    def no_network(*args, **kwargs):
        raise AssertionError('Unexpected network call in offline regression tests')
    monkeypatch.setattr(socket, 'create_connection', no_network)
    connect = socket.socket.connect
    def guarded_connect(sock, address):
        # Windows asyncio implements its local wakeup pipe with socketpair.
        if isinstance(address, tuple) and address[0] in ('127.0.0.1', '::1'):
            return connect(sock, address)
        return no_network()
    monkeypatch.setattr(socket.socket, 'connect', guarded_connect)
@pytest.fixture
def state():
    from triz.pipeline import create_run
    return create_run("반도체 웨이퍼 세정에서 파티클을 줄이면 미세 패턴 손상이 발생합니다.", mode="FULL")

def pytest_sessionfinish(session, exitstatus):
    from triz import store
    store.engine.dispose()
    TEST_DIR.cleanup()
