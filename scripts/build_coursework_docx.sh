#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INPUT="${ROOT_DIR}/manuscript/coursework.md"
OUTPUT="${1:-${ROOT_DIR}/build/coursework-final.docx}"

mkdir -p "$(dirname "${OUTPUT}")"

pandoc "${INPUT}" \
  --from=markdown+tex_math_dollars+pipe_tables+implicit_figures \
  --to=docx \
  --standalone \
  --metadata=lang:ru-RU \
  --resource-path="${ROOT_DIR}:${ROOT_DIR}/manuscript:${ROOT_DIR}/article:${ROOT_DIR}/article/figures" \
  --output="${OUTPUT}"

printf 'Built %s\n' "${OUTPUT}"
