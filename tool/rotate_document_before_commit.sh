#!/usr/bin/env bash
#
# Usage:
#   ./tool/rotate_document_before_commit.sh
#
# Purpose:
#   Rotate documents under the configured directory before commit.
#   - Finalize <dir>/previous/ into <dir>/<HEAD shortsha>-<HEAD slug>/
#   - Move current working files from <dir>/ root into <dir>/previous/
#
# Exit non-zero if rotation cannot be completed safely.

set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
cd "$repo_root"

config_file="${ROTATE_DOCUMENT_CONFIG:-.document-rotation.env}"
if [[ -f "$config_file" ]]; then
  set -a
  # shellcheck disable=SC1090
  . "$config_file"
  set +a
fi

doc_dir="${ROTATE_DOCUMENT_DIR:-document}"
doc_dir="${doc_dir%/}"

if [[ -z "$doc_dir" ]]; then
  echo "rotate_document_before_commit: ROTATE_DOCUMENT_DIR must not be empty" >&2
  exit 1
fi

previous_dir="$doc_dir/previous"

if [[ ! -d "$doc_dir" ]]; then
  exit 0
fi

has_head=0
if git rev-parse --verify HEAD >/dev/null 2>&1; then
  has_head=1
fi

slugify_head() {
  git log -1 --format=%f HEAD
}

finalize_previous() {
  local shortsha slug archive_dir

  [[ -d "$previous_dir" ]] || return 0

  shortsha=$(git rev-parse --short HEAD)
  slug=$(slugify_head)
  archive_dir="$doc_dir/${shortsha}-${slug}"

  if [[ -e "$archive_dir" ]]; then
    echo "rotate_document_before_commit: archive directory already exists: $archive_dir" >&2
    exit 1
  fi

  mv "$previous_dir" "$archive_dir"
}

move_root_entries_to_previous() {
  local moved=0
  mkdir -p "$previous_dir"

  shopt -s nullglob dotglob
  for path in "$doc_dir"/*; do
    local base
    base=$(basename "$path")

    if [[ "$base" == "previous" ]]; then
      continue
    fi

    if [[ "$base" =~ ^[0-9a-f]{7,40}- ]]; then
      continue
    fi

    mv "$path" "$previous_dir"/
    moved=1
  done
  shopt -u nullglob dotglob

  if [[ "$moved" -eq 0 ]]; then
    rmdir "$previous_dir" 2>/dev/null || true
  fi
}

if [[ "$has_head" -eq 1 ]]; then
  finalize_previous
fi

move_root_entries_to_previous
