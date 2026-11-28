#!/usr/bin/env bash
# Render README badges as SVG files, offline, with shields.io's own renderer (badge-maker).
#
#   bash scripts/badges.sh SPEC OUTDIR
#
# SPEC has one badge per line: name|label|message|color (color: a badge-maker name such as
# brightgreen, red, blue, lightgrey, or #rgb / #rrggbb). Each becomes OUTDIR/<name>.svg.
# Empty lines and lines starting with # are skipped. CI (check.yml, job "badges") writes SPEC
# and pushes OUTDIR to the orphan branch "badges".
set -euo pipefail

BADGE_MAKER="badge-maker@6.0.0" # pinned; bump on purpose

spec=${1:?usage: badges.sh SPEC OUTDIR}
out=${2:?usage: badges.sh SPEC OUTDIR}
mkdir -p "$out"

while IFS='|' read -r name label message color || [ -n "${name:-}" ]; do
  case "$name" in ''|'#'*) continue ;; esac
  if ! [[ "$name" =~ ^[a-z0-9-]+$ ]]; then
    echo "badges.sh: bad badge name: $name" >&2
    exit 1
  fi
  npx -y -p "$BADGE_MAKER" badge "$label" "$message" ":$color" > "$out/$name.svg"
  echo "wrote $out/$name.svg ($label: $message)"
done < "$spec"
