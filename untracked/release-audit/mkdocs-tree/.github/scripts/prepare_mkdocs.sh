#!/usr/bin/env bash
set -euo pipefail

# Stage root-level docs into docs/ for MkDocs (changelog + security policy).
cp CHANGELOG.md docs/changelog.md
cp SECURITY.md docs/security.md

python - <<'PY'
from pathlib import Path

path = Path("docs/security.md")
path.write_text(path.read_text(encoding="utf-8").replace("](docs/", "]("), encoding="utf-8")
PY
