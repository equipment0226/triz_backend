"""Search files stay public without exposing application APIs or other files."""
import xml.etree.ElementTree as ET

import pytest
from fastapi.testclient import TestClient

from api.main import app
from triz.settings import settings


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(settings, "app_token", "test-required-app-token")
    monkeypatch.setattr(settings, "require_user_auth", True)
    # Do not start background workers or recovery during public route checks.
    return TestClient(app)


@pytest.mark.parametrize("path,content_type", [
    ("/googledb97084bf62cb561.html", "text/html"),
    ("/robots.txt", "text/plain"),
    ("/sitemap.xml", "application/xml"),
])
def test_search_files_are_public_with_head_support(client, path, content_type):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 200
    assert response.headers["content-type"].startswith(content_type)
    head = client.head(path, follow_redirects=False)
    assert head.status_code == 200
    assert head.content == b""
    assert head.headers["content-length"] == str(len(response.content))
    assert client.post(path).status_code == 405


def test_verification_body_and_canonical_sitemap(client):
    assert client.get("/googledb97084bf62cb561.html").text.strip() == (
        "google-site-verification: googledb97084bf62cb561.html"
    )
    sitemap = ET.fromstring(client.get("/sitemap.xml").content)
    locations = sitemap.findall("{*}url/{*}loc")
    assert [entry.text for entry in locations] == ["https://trizstudio.online/"]
    robots = client.get("/robots.txt").text
    assert "Disallow: /\n" not in robots
    assert "Sitemap: https://trizstudio.online/sitemap.xml" in robots


def test_search_routes_do_not_expose_api_or_arbitrary_files(client):
    assert client.get("/api/runs").status_code == 401
    for path in ("/google-other.html", "/public/.env", "/sitemap.xml/extra"):
        assert client.get(path).status_code == 404
