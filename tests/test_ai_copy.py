import json

from utils import ai_copy


class _Report:
    health_score = 90
    headline = "Original headline"

    @staticmethod
    def top_tip():
        return "Review cutting waste"


class _Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self):
        return json.dumps({
            "choices": [{"message": {"content": "Review the highest-waste bars."}}]
        }).encode("utf-8")


def test_ai_copy_rejects_non_network_url_scheme(monkeypatch):
    monkeypatch.setenv("REBARAGENT_AI_API_KEY", "test-secret")
    monkeypatch.setenv("REBARAGENT_AI_BASE_URL", "file:///tmp/exfil")
    called = []
    monkeypatch.setattr(ai_copy.urllib.request, "urlopen", lambda *a, **k: called.append(True))

    report = _Report()
    ai_copy.maybe_enrich_report(report)

    assert called == []
    assert report.headline == "Original headline"


def test_ai_copy_rejects_remote_plain_http(monkeypatch):
    monkeypatch.setenv("REBARAGENT_AI_API_KEY", "test-secret")
    monkeypatch.setenv("REBARAGENT_AI_BASE_URL", "http://api.example.com/v1")
    called = []
    monkeypatch.setattr(ai_copy.urllib.request, "urlopen", lambda *a, **k: called.append(True))

    ai_copy.maybe_enrich_report(_Report())

    assert called == []


def test_ai_copy_allows_https_provider_with_timeout(monkeypatch):
    monkeypatch.setenv("REBARAGENT_AI_API_KEY", "test-secret")
    monkeypatch.setenv("REBARAGENT_AI_BASE_URL", "https://api.example.com/v1")
    calls = []

    def fake_urlopen(request, timeout):
        calls.append((request.full_url, timeout, request.get_header("Authorization")))
        return _Response()

    monkeypatch.setattr(ai_copy.urllib.request, "urlopen", fake_urlopen)
    report = _Report()
    ai_copy.maybe_enrich_report(report)

    assert calls == [("https://api.example.com/v1/chat/completions", 4, "Bearer test-secret")]
    assert report.headline == "Review the highest-waste bars."


def test_ai_copy_silently_rejects_malformed_endpoint(monkeypatch):
    monkeypatch.setenv("REBARAGENT_AI_API_KEY", "test-secret")
    monkeypatch.setenv("REBARAGENT_AI_BASE_URL", "http://[invalid")
    report = _Report()

    ai_copy.maybe_enrich_report(report)

    assert report.headline == "Original headline"
