#!/usr/bin/env bash
set -euo pipefail
ROOT="/home/ubuntu/.openclaw/workspace/projects/bullpen-dashboard"
python3 "$ROOT/build_dashboard_data.py"
cd "$ROOT"
git add dashboard-data.json index.html README.md .nojekyll build_dashboard_data.py || true
if git diff --cached --quiet; then
  echo "No dashboard changes to publish"
  exit 0
fi
git commit -m "Publish dashboard update"
git push
