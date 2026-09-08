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
os.environ["LLM_API_KEY"] = "offline-test"
os.environ["TRIZ_SERVICE_TOKEN"] = "offline-test-service"
import pytest
@pytest.fixture(autouse=True)
def no_paid_calls(monkeypatch):
    from triz import llm
    monkeypatch.setattr(llm, "chat_json", lambda **kwargs: (_ for _ in ()).throw(AssertionError("Unexpected real LLM call")))
@pytest.fixture
def state():
    from triz.pipeline import create_run
    return create_run("반도체 웨이퍼 세정에서 파티클을 줄이면 미세 패턴 손상이 발생합니다.", mode="FULL")

def pytest_sessionfinish(session, exitstatus):
    from triz import store
    store.engine.dispose()
    TEST_DIR.cleanup()
