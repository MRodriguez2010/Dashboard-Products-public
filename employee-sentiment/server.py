"""Run the local Employee Sentiment Analysis portfolio demonstration."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit
from reporting.deck import make_deck
from reporting.model import ROOT, analyze, finding

ASSETS = {"/": ("index.html", "text/html"), "/app.js": ("app.js", "text/javascript"),
          "/style.css": ("style.css", "text/css")}


class Handler(BaseHTTPRequestHandler):
    def respond(self, data, content_type, status=200, filename=None):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        if filename:
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        asset = ASSETS.get(urlsplit(self.path).path)
        if not asset:
            return self.send_error(404)
        self.respond((ROOT / "static" / asset[0]).read_bytes(), asset[1] + "; charset=utf-8")

    def do_POST(self):
        if self.path not in ("/analysis", "/presentation"):
            return self.send_error(404)
        try:
            size = int(self.headers.get("Content-Length", 0))
            if not 0 < size <= 4096:
                raise ValueError("Invalid request length.")
            payload = json.loads(self.rfile.read(size))
            if not isinstance(payload, dict):
                raise ValueError("Expected report settings.")
            report = analyze(**payload)
        except (ValueError, TypeError, KeyError):
            return self.respond(b'{"error":"Check the selected company, peer group, range and report type."}', "application/json", 400)
        if self.path == "/analysis":
            self.respond(json.dumps({**report, "finding": finding(report)}).encode(), "application/json")
        else:
            self.respond(make_deck(report), "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                         filename="employee-sentiment-analysis.pptx")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    print(f"Open http://127.0.0.1:{args.port}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", args.port), Handler).serve_forever()
