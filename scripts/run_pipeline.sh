#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/run_pipeline.sh '<arxiv url or id>'"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="$1"

if [[ -d "${ROOT_DIR}/.venv-paper-reading" ]]; then
  source "${ROOT_DIR}/.venv-paper-reading/bin/activate"
fi

python "${ROOT_DIR}/scripts/prepare_workspace.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/fetch_sources.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_references.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_images.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/build_report_skeleton.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/validate_report_text.py" --input "${INPUT}" --root "${PWD}"

echo "Pipeline complete."
echo "Tip: before reading/editing Chinese reports in Windows PowerShell, run:"
echo "  \$utf8=[System.Text.UTF8Encoding]::new(\$false); chcp 65001 > \$null; [Console]::InputEncoding=\$utf8; [Console]::OutputEncoding=\$utf8; \$OutputEncoding=\$utf8"
echo "Re-run the text validator before delivery if the report was edited manually."
