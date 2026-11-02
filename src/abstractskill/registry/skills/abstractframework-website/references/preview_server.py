#!/usr/bin/env python3
"""Serve a static site directory locally with HTTP Range support (videos seek), no caching.

Usage: preview_server.py <directory> [--port 56265] [--bind 127.0.0.1]
Read-only: it never writes into the directory. Stop it with Ctrl-C or kill <pid>.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from functools import partial
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer


class RangeHandler(SimpleHTTPRequestHandler):
    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        self.send_header("Accept-Ranges", "bytes")
        super().end_headers()

    def send_head(self):  # noqa: ANN201 - stdlib signature
        rng = self.headers.get("Range")
        if not rng:
            return super().send_head()
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        try:
            size = os.path.getsize(path)
        except OSError:
            self.send_error(HTTPStatus.NOT_FOUND, "File not found")
            return None
        m = re.match(r"bytes=(\d*)-(\d*)$", rng.strip())
        if not m:
            return super().send_head()
        start = int(m.group(1)) if m.group(1) else max(0, size - int(m.group(2) or 0))
        end = int(m.group(2)) if m.group(1) and m.group(2) else size - 1
        end = min(end, size - 1)
        if start > end or start >= size:
            self.send_response(HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE)
            self.send_header("Content-Range", f"bytes */{size}")
            self.end_headers()
            return None
        fh = open(path, "rb")
        fh.seek(start)
        self.send_response(HTTPStatus.PARTIAL_CONTENT)
        self.send_header("Content-Type", self.guess_type(path))
        self.send_header("Content-Range", f"bytes {start}-{end}/{size}")
        self.send_header("Content-Length", str(end - start + 1))
        self.end_headers()
        self._range_left = end - start + 1
        return fh

    def copyfile(self, source, outputfile) -> None:  # noqa: ANN001 - stdlib signature
        left = getattr(self, "_range_left", None)
        if left is None:
            return super().copyfile(source, outputfile)
        while left > 0:
            chunk = source.read(min(65536, left))
            if not chunk:
                break
            outputfile.write(chunk)
            left -= len(chunk)
        self._range_left = None

    def log_message(self, fmt, *args) -> None:  # noqa: ANN001 - quiet by default
        if os.environ.get("PREVIEW_VERBOSE"):
            super().log_message(fmt, *args)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("directory")
    ap.add_argument("--port", type=int, default=56265)
    ap.add_argument("--bind", default="127.0.0.1")
    a = ap.parse_args()
    directory = os.path.abspath(a.directory)
    if not os.path.isdir(directory):
        print(f"not a directory: {directory}", file=sys.stderr)
        return 2
    handler = partial(RangeHandler, directory=directory)
    httpd = ThreadingHTTPServer((a.bind, a.port), handler)
    print(f"serving {directory} at http://{a.bind}:{a.port}/ (pid {os.getpid()})", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
