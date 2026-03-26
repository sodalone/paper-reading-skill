#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/run_pipeline.sh '<arxiv url or id>'"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="$1"

if [[ -d "${ROOT_DIR}/.venv-paper-reviewer" ]]; then
  source "${ROOT_DIR}/.venv-paper-reviewer/bin/activate"
fi

python "${ROOT_DIR}/scripts/prepare_workspace.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/fetch_sources.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_references.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_images.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/build_report_skeleton.py" --input "${INPUT}" --root "${PWD}"

echo "Pipeline complete."
