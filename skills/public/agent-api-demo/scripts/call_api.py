"""CLI adapter used by the agent-api-demo skill to call the Gateway API."""

from __future__ import annotations

import argparse
import json
import os
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Call DeerFlow's agent notes API")
    parser.add_argument("action", choices=("list", "get", "create", "update", "delete"))
    parser.add_argument("--id", dest="note_id")
    parser.add_argument("--query")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--title")
    parser.add_argument("--content")
    return parser


def _validate_and_payload(action: str, args: argparse.Namespace) -> dict | None:
    if action in {"get", "update", "delete"} and not args.note_id:
        raise ValueError(f"{action} requires --id")
    if action == "create":
        if args.title is None or args.content is None:
            raise ValueError("create requires --title and --content")
        return {"title": args.title, "content": args.content}
    if action == "update":
        payload = {key: value for key, value in {"title": args.title, "content": args.content}.items() if value is not None}
        if not payload:
            raise ValueError("update requires --title and/or --content")
        return payload
    return None


def _url(action: str, args: argparse.Namespace) -> str:
    base_url = os.environ.get("DEERFLOW_API_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
    url = f"{base_url}/api/agent-notes"
    if action in {"get", "update", "delete"}:
        url += f"/{args.note_id}"
    if action == "list":
        params = {key: value for key, value in {"q": args.query, "limit": args.limit, "offset": args.offset}.items() if value is not None}
        url += f"?{urlencode(params)}"
    return url


def main() -> int:
    args = _parser().parse_args()
    try:
        payload = _validate_and_payload(args.action, args)
        method = {"list": "GET", "get": "GET", "create": "POST", "update": "PATCH", "delete": "DELETE"}[args.action]
        headers = {"Accept": "application/json"}
        token = os.environ.get("DEERFLOW_API_TOKEN")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
        if data is not None:
            headers["Content-Type"] = "application/json"
        request = Request(_url(args.action, args), data=data, headers=headers, method=method)
        with urlopen(request, timeout=30) as response:
            raw = response.read()
            if raw:
                print(json.dumps(json.loads(raw), ensure_ascii=False, indent=2))
            return 0
    except (ValueError, HTTPError, URLError, TimeoutError) as exc:
        if isinstance(exc, HTTPError):
            try:
                detail = exc.read().decode("utf-8", errors="replace").strip()
            except OSError as read_error:
                # Some Windows HTTP stacks reset the connection while the
                # error body is being read. Keep the original HTTP status
                # visible instead of masking it with WinError 10054.
                detail = f"响应正文不可用：{read_error}"
            if not detail:
                detail = "响应正文为空"
            if exc.code in {401, 403} and not os.environ.get("DEERFLOW_API_TOKEN"):
                detail += "；认证已启用，请先设置 DEERFLOW_API_TOKEN（PAT）"
            print(f"HTTP {exc.code}: {detail}", file=sys.stderr)
        else:
            print(str(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
