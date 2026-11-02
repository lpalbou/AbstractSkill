#!/usr/bin/env python3
"""Static checks for the abstractframework.ai site worktree. Read-only.

Usage: check_site.py <site dir> [--min-version-for <package>=<x.y.z> ...]
Fails (exit 1) on: a local link or asset that does not resolve, a page without exactly one
<title>, an <img> without width/height or whose file is missing, leftover TODO/PENDING/COMING SOON
markers, and version strings below the given floors next to a package name.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from html.parser import HTMLParser


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.titles = 0
        self.links: list[str] = []
        self.imgs: list[tuple[str, bool]] = []

    def handle_starttag(self, tag, attrs):  # noqa: ANN001
        d = dict(attrs)
        if tag == "title":
            self.titles += 1
        if tag in ("a", "link") and d.get("href"):
            self.links.append(d["href"])
        if tag in ("script", "source", "video", "audio") and d.get("src"):
            self.links.append(d["src"])
        if tag == "img" and d.get("src"):
            self.imgs.append((d["src"], bool(d.get("width") and d.get("height"))))


def local(ref: str) -> str | None:
    if re.match(r"^(https?:|mailto:|tel:|data:|javascript:|#)", ref):
        return None
    return ref.split("#", 1)[0].split("?", 1)[0] or None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("site")
    ap.add_argument("--min-version-for", action="append", default=[], metavar="PKG=X.Y.Z")
    a = ap.parse_args()
    root = os.path.abspath(a.site)
    floors = dict(x.split("=", 1) for x in a.min_version_for)
    problems: list[str] = []
    pages = [f for f in os.listdir(root) if f.endswith(".html")]
    for page in sorted(pages):
        text = open(os.path.join(root, page), encoding="utf-8", errors="replace").read()
        c = Collector()
        c.feed(text)
        if c.titles != 1:
            problems.append(f"{page}: {c.titles} <title> tags")
        for marker in ("TODO", "PENDING-W", "COMING SOON", "coming soon", "FIXME"):
            if marker in text:
                problems.append(f"{page}: leftover marker {marker!r}")
        for ref in c.links:
            rel = local(ref)
            if rel and not os.path.exists(os.path.join(root, rel.lstrip("/"))):
                problems.append(f"{page}: broken local link {ref}")
        for src, sized in c.imgs:
            rel = local(src)
            if rel and not os.path.exists(os.path.join(root, rel.lstrip("/"))):
                problems.append(f"{page}: missing image {src}")
            if not sized:
                problems.append(f"{page}: <img {src}> without width/height")
        for pkg, floor in floors.items():
            for m in re.finditer(re.escape(pkg) + r"[^0-9\n]{0,40}?(\d+\.\d+\.\d+)", text):
                found = tuple(int(x) for x in m.group(1).split("."))
                if found < tuple(int(x) for x in floor.split(".")):
                    problems.append(f"{page}: {pkg} {m.group(1)} is below the released {floor}")
    for p in problems:
        print(p)
    print(f"{len(pages)} pages, {len(problems)} problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
