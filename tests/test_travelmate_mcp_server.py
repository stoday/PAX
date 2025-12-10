from __future__ import annotations

import json
from pathlib import Path

import pytest

from travelmate import get_travel_project_list as project_list
from travelmate import get_travel_web_cookie as cookie_script
from travelmate import get_travel_web_newbasic as newbasic_script
from travelmate import mcp_server
from travelmate import travel_apply_web as apply_script


def test_refresh_project_list(tmp_path, monkeypatch):
    """Ensure refresh tool saves fetched projects and reports count/path."""
    fake_projects = [{"code": "A1"}]

    monkeypatch.setattr(project_list, "fetch_project_list", lambda: fake_projects)
    monkeypatch.setattr(project_list, "PROJECT_LIST_PATH", tmp_path / "project_list.json")

    result = mcp_server.refresh_project_list()

    assert result["count"] == len(fake_projects)
    saved = json.loads(Path(result["path"]).read_text(encoding="utf-8"))
    assert saved == fake_projects


def test_capture_travel_cookies(monkeypatch, tmp_path):
    """Ensure cookie tool runs selenium flow and returns env path."""
    called = {"flag": False}

    def fake_main() -> None:
        called["flag"] = True

    monkeypatch.setattr(cookie_script, "main", fake_main)
    monkeypatch.setattr(cookie_script, "ENV_PATH", tmp_path / ".env_cookie")

    message = mcp_server.capture_travel_cookies()

    assert called["flag"] is True
    assert str(tmp_path / ".env_cookie") in message


def test_fetch_new_basic_info(monkeypatch):
    """Ensure new basic tool returns upstream payload unchanged."""
    expected = {"NAME": "Tester"}
    monkeypatch.setattr(newbasic_script, "fetch_newbasic", lambda: expected)

    result = mcp_server.fetch_new_basic_info()

    assert result is expected


class _Response:
    def __init__(self, status_code: int, payload: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload
        self.text = text

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


def test_submit_travel_application_with_override(monkeypatch):
    """Ensure payload overrides and timeout propagate and JSON response parsed."""
    captured = {}
    response = _Response(200, payload={"ok": True}, text="{\"ok\": true}")

    def fake_submit_application(*, payload=None, timeout: int, **_):
        captured["payload"] = payload
        captured["timeout"] = timeout
        return response

    monkeypatch.setattr(apply_script, "submit_application", fake_submit_application)

    payload_json = json.dumps({"BasicData": "value"})
    result = mcp_server.submit_travel_application(payload_json=payload_json, timeout=10)

    assert captured["payload"] == json.loads(payload_json)
    assert captured["timeout"] == 10
    assert result == {"status_code": 200, "body": {"ok": True}}


def test_submit_travel_application_handles_text(monkeypatch):
    """Ensure submit tool falls back to response text when JSON unavailable."""
    response = _Response(200, payload=None, text="ok")
    monkeypatch.setattr(apply_script, "submit_application", lambda **_: response)

    result = mcp_server.submit_travel_application()

    assert result == {"status_code": 200, "body": "ok"}


@pytest.mark.parametrize("bad_input", ["[1,2,3]", "invalid", "123"])
def test_submit_travel_application_rejects_non_object_json(bad_input):
    """Ensure non-object or invalid JSON input raises a validation error."""
    with pytest.raises((TypeError, ValueError)):
        mcp_server.submit_travel_application(payload_json=bad_input)
