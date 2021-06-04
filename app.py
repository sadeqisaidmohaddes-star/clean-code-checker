"""Clean Code Checker — web server.

Run ``python app.py`` and open http://localhost:8000. The server has no
third-party dependencies: it uses Python's standard library only.

  * ``GET /``            -> the single-page UI
  * ``GET /api/analyze`` -> JSON report for ?repo=<url>&token=<optional>
"""

from __future__ import annotations

import json
import mimetypes
import os
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from cleancode import GitHubError, analyze_repo

HOST = "127.0.0.1"
PORT = int(os.environ.get("PORT", "8000"))
WEB_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "web")


class Handler(BaseHTTPRequestHandler):
    server_version = "CleanCodeChecker/1.0"

    def do_GET(self) -> None:  # noqa: N802 (name fixed by BaseHTTPRequestHandler)
        route = urlparse(self.path)
        if route.path == "/api/analyze":
            self._handle_analyze(parse_qs(route.query))
        else:
            self._serve_static(route.path)

    # -- routes ------------------------------------------------------------

    def _handle_analyze(self, query: dict[str, list[str]]) -> None:
        repo = (query.get("repo", [""])[0]).strip()
        token = (query.get("token", [""])[0]).strip() or None
        if not repo:
            self._send_json({"error": "Missing 'repo' parameter."}, status=400)
            return
        try:
            report = analyze_repo(repo, token)
            self._send_json(report)
        except GitHubError as error:
            self._send_json({"error": str(error)}, status=400)
        except Exception as error:  # noqa: BLE001 — never leak a stack trace to the client
            self._log_unexpected(error)
            self._send_json({"error": "Unexpected server error while analysing the repo."}, status=500)

    def _serve_static(self, path: str) -> None:
        relative = "index.html" if path in ("/", "") else path.lstrip("/")
        target = os.path.normpath(os.path.join(WEB_DIR, relative))
        # Require a real path-separator boundary so a sibling like "webapp"
        # can't satisfy a bare prefix match and escape WEB_DIR.
        if not target.startswith(WEB_DIR + os.sep):
            self._send_bytes(b"Not found", 404, "text/plain")
            return
        content_type = mimetypes.guess_type(target)[0] or "application/octet-stream"
        try:
            with open(target, "rb") as handle:
                body = handle.read()
        except OSError:
            # Missing file, a directory, a permission error, or a delete-between-
            # check-and-open race all resolve to a clean 404.
            self._send_bytes(b"Not found", 404, "text/plain")
            return
        self._send_bytes(body, 200, content_type)

    # -- response helpers --------------------------------------------------

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self._send_bytes(body, status, "application/json; charset=utf-8")

    def _send_bytes(self, body: bytes, status: int, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _log_unexpected(self, error: Exception) -> None:
        sys.stderr.write(f"[error] {type(error).__name__}: {error}\n")

    def log_message(self, fmt: str, *args) -> None:  # quieter, single-line logs
        sys.stderr.write(f"{self.address_string()} - {fmt % args}\n")


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    url = f"http://{HOST}:{PORT}"
    print(f"Clean Code Checker running at {url}")
    print("Press Ctrl+C to stop.")
    if "--no-browser" not in sys.argv:
        try:
            webbrowser.open(url)
        except Exception:  # noqa: BLE001 — opening a browser is best-effort
            pass
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
        server.shutdown()


if __name__ == "__main__":
    main()
