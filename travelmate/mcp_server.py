#!/usr/bin/env python3
"""Expose the travelmate utilities as MCP tools."""
from __future__ import annotations

import argparse
import json
from typing import Any, Dict

from mcp.server.fastmcp import FastMCP

from travelmate import get_travel_project_list as project_list
from travelmate import get_travel_web_cookie as cookie_script
from travelmate import get_travel_web_newbasic as newbasic_script
from travelmate import travel_apply_web as apply_script

mcp = FastMCP("TravelMate")


def _write_project_list(projects: list[Dict[str, Any]]) -> Dict[str, Any]:
    payload = json.dumps(projects, ensure_ascii=False, indent=2)
    project_list.PROJECT_LIST_PATH.write_text(payload, encoding="utf-8")
    return {
        "count": len(projects),
        "path": str(project_list.PROJECT_LIST_PATH),
    }


@mcp.tool(
    description=(
        "Fetch Context.ProjectCode entries from the travel apply page and write them to "
        "project_list.json. Example: call refresh_project_list() with no arguments; it returns "
        "{\"count\": <int>, \"path\": \".../project_list.json\"}."
    )
)
def refresh_project_list() -> Dict[str, Any]:
    """Fetch Context.ProjectCode entries and persist project_list.json."""
    projects = project_list.fetch_project_list()
    return _write_project_list(projects)


@mcp.tool(
    description=(
        "Open a browser, let the user log in, then persist cookies into .env_cookie for reuse. "
        "Example: call capture_travel_cookies() with no arguments; it returns the .env_cookie path."
    )
)
def capture_travel_cookies() -> str:
    """Launch Selenium login helper and persist cookies to .env_cookie."""
    cookie_script.main()
    return f"Cookies saved to {cookie_script.ENV_PATH}"


@mcp.tool(
    description=(
        "Call the GetNewBasic API using existing travel cookies, store the response fields in "
        ".env_cookie, and return the parsed JSON object. Example: fetch_new_basic_info() -> "
        "{\"NAME\": \"...\", \"DEPTNAME\": \"...\", ...}."
    )
)
def fetch_new_basic_info() -> Dict[str, Any]:
    """Call GetNewBasic API, store its response, and return the parsed payload."""
    return newbasic_script.fetch_newbasic()


@mcp.tool(
    description=(
        "Submit the travel application payload to the DC Save endpoint. "
        "If payload_json is provided, it must be a JSON object string to override the default "
        "payload; otherwise the payload is built from local defaults/.env_cookie. "
        "Example: submit_travel_application() or submit_travel_application(payload_json='{\"AppData\":{\"IS_SUBMIT\":\"N\"}}', timeout=20). "
        "Returns status_code and response body."
    )
)
def submit_travel_application(payload_json: str | None = None, timeout: int = 15) -> Dict[str, Any]:
    """Submit the current payload to the travel application endpoint."""
    payload_override: Dict[str, Any] | None = None
    if payload_json:
        try:
            parsed = json.loads(payload_json)
        except json.JSONDecodeError as exc:
            raise ValueError("payload_json must be valid JSON") from exc
        if not isinstance(parsed, dict):
            raise TypeError("payload_json must describe a JSON object")
        payload_override = parsed

    response = apply_script.submit_application(payload=payload_override, timeout=timeout)
    try:
        body = response.json()
    except ValueError:
        body = response.text
    return {"status_code": response.status_code, "body": body}


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Travelmate MCP server")
    parser.add_argument("--transport", choices=["stdio", "sse"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_kwargs: Dict[str, Any] = {"transport": args.transport}
    if args.transport == "sse":
        run_kwargs.update({"host": args.host, "port": args.port})
    mcp.run(**run_kwargs)


if __name__ == "__main__":
    main()
