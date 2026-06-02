#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
MANUSCRIPT="${ROOT_DIR}/manuscript/coursework.md"
DOCX="${1:-${ROOT_DIR}/build/coursework-final.docx}"
BUILD_SCRIPT="${ROOT_DIR}/scripts/build_coursework_docx.sh"

status=0

printf 'Final coursework audit\n'
printf 'manuscript=%s\n' "${MANUSCRIPT}"
printf 'docx=%s\n' "${DOCX}"

if [[ ! -s "${MANUSCRIPT}" ]]; then
  printf 'ERROR: manuscript is missing or empty\n' >&2
  exit 1
fi

word_count="$(wc -w < "${MANUSCRIPT}" || printf '0')"
reference_count="$(
  awk '
    /^## Список литературы/ { in_refs=1; next }
    /^## Приложение/ { in_refs=0 }
    in_refs && /^[0-9]+\./ { count++ }
    END { print count + 0 }
  ' "${MANUSCRIPT}" || printf '0'
)"
table_count="$(rg -n '^\*Таблица [0-9]+\.' "${MANUSCRIPT}" | wc -l || true)"
figure_count="$(rg -n '^!\[Рисунок [0-9]+\.' "${MANUSCRIPT}" | wc -l || true)"

printf 'word_count=%s\n' "${word_count}"
printf 'reference_count=%s\n' "${reference_count}"
printf 'table_captions=%s\n' "${table_count}"
printf 'figure_captions=%s\n' "${figure_count}"

if [[ "${reference_count}" -lt 15 ]]; then
  printf 'ERROR: reference list is unexpectedly short\n' >&2
  status=1
fi

placeholder_audit="${ROOT_DIR}/build/coursework-placeholder-audit.txt"
mkdir -p "${ROOT_DIR}/build"
if rg -n 'TODO|FIXME|TBD|заглуш|дописать|уточнить позже|placeholder|\{\{' "${MANUSCRIPT}" > "${placeholder_audit}"; then
  printf 'ERROR: placeholder-like text found: %s\n' "${placeholder_audit}" >&2
  status=1
else
  rm -f "${placeholder_audit}"
fi

duplicate_word_audit="${ROOT_DIR}/build/coursework-duplicate-word-audit.txt"
perl -CSDA -ne 'while (/\b([[:alpha:]]{2,})\b\s+\b\1\b/giu) { print "$.:$&\n" }' "${MANUSCRIPT}" > "${duplicate_word_audit}" || true
duplicate_word_count="$(wc -l < "${duplicate_word_audit}" || printf '0')"
printf 'duplicate_word_count=%s\n' "${duplicate_word_count}"
if [[ "${duplicate_word_count}" -gt 0 ]]; then
  printf 'ERROR: repeated adjacent words found: %s\n' "${duplicate_word_audit}" >&2
  status=1
else
  rm -f "${duplicate_word_audit}"
fi

punctuation_audit="${ROOT_DIR}/build/coursework-punctuation-audit.txt"
perl -CSDA -ne '
  next if /^\|/;
  while (/[[:space:]]+[,.;:]|,,|\.{2,}|;;|::|\(\s+|\s+\)/g) {
    print "$.:$&\n";
  }
' "${MANUSCRIPT}" > "${punctuation_audit}" || true
punctuation_issue_count="$(wc -l < "${punctuation_audit}" || printf '0')"
printf 'punctuation_issue_count=%s\n' "${punctuation_issue_count}"
if [[ "${punctuation_issue_count}" -gt 0 ]]; then
  printf 'ERROR: punctuation artifacts found: %s\n' "${punctuation_audit}" >&2
  status=1
else
  rm -f "${punctuation_audit}"
fi

missing_images=0
while IFS= read -r image_path; do
  if [[ ! -f "${ROOT_DIR}/${image_path}" ]]; then
    printf 'ERROR: missing image referenced by manuscript: %s\n' "${image_path}" >&2
    missing_images=1
  fi
done < <(sed -n 's/.*](\([^)]*\.png\)).*/\1/p' "${MANUSCRIPT}" || true)

if [[ "${missing_images}" -ne 0 ]]; then
  status=1
fi

"${BUILD_SCRIPT}" "${DOCX}"
unzip -t "${DOCX}" >/dev/null

docx_media_count="$(unzip -Z1 "${DOCX}" 2>/dev/null | grep -c '^word/media/' || true)"
printf 'docx_media_count=%s\n' "${docx_media_count}"

if [[ "${docx_media_count}" -lt "${figure_count}" ]]; then
  printf 'ERROR: DOCX contains fewer embedded media files than referenced figures\n' >&2
  status=1
fi

docx_math_count="$(unzip -p "${DOCX}" word/document.xml | rg -o '<m:oMath' | wc -l || true)"
printf 'docx_math_count=%s\n' "${docx_math_count}"
if [[ "${docx_math_count}" -lt 20 ]]; then
  printf 'ERROR: DOCX contains unexpectedly few Word math objects\n' >&2
  status=1
fi

raw_tex_audit="${ROOT_DIR}/build/coursework-docx-raw-tex-audit.txt"
: > "${raw_tex_audit}"
raw_tex_found=0
for needle in '\operatorname' '\frac' '\alpha' '\sum' '\mathrm'; do
  if unzip -p "${DOCX}" word/document.xml | rg -F "${needle}" >> "${raw_tex_audit}"; then
    raw_tex_found=1
  fi
done

if [[ "${raw_tex_found}" -ne 0 ]]; then
  printf 'ERROR: raw TeX markers found in DOCX XML: %s\n' "${raw_tex_audit}" >&2
  status=1
else
  rm -f "${raw_tex_audit}"
fi

if [[ "${status}" -ne 0 ]]; then
  printf 'Final audit failed\n' >&2
  exit "${status}"
fi

printf 'Final audit passed\n'
