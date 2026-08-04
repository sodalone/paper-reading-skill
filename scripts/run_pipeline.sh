#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: bash scripts/run_pipeline.sh '<arxiv url or id>' [--workspace-name '<directory name>']"
  exit 1
fi

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="$1"
shift

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workspace-name)
      if [[ $# -lt 2 || -z "$2" ]]; then
        echo "Error: --workspace-name requires a directory name"
        exit 2
      fi
      export PAPER_READING_WORKSPACE_NAME="$2"
      shift 2
      ;;
    *)
      echo "Error: unknown argument: $1"
      exit 2
      ;;
  esac
done

if [[ -d "${ROOT_DIR}/.venv-paper-reading" ]]; then
  source "${ROOT_DIR}/.venv-paper-reading/bin/activate"
fi

python "${ROOT_DIR}/scripts/prepare_workspace.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/fetch_sources.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_references.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/extract_images.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/build_report_skeleton.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/validate_report_text.py" --input "${INPUT}" --root "${PWD}"
python "${ROOT_DIR}/scripts/validate_report.py" --input "${INPUT}" --root "${PWD}"

echo "Pipeline complete."
echo "Tip: before reading/editing Chinese reports in Windows PowerShell, run:"
echo "  \$utf8=[System.Text.UTF8Encoding]::new(\$false); chcp 65001 > \$null; [Console]::InputEncoding=\$utf8; [Console]::OutputEncoding=\$utf8; \$OutputEncoding=\$utf8"
echo "Re-run the text validator before delivery if the report was edited manually."
