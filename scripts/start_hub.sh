#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."

echo ""
echo "  Veridag The Hub — http://127.0.0.1:8787/hub"
echo ""

python3 -m pip install -q -r requirements.txt
exec python3 -m app.main
