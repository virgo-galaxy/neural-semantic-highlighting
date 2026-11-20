#!/usr/bin/env bash
set -euo pipefail

target=${1:-preview}
files=(app.ts app.tsx)

build() {
  printf 'Building %s\n' "$target"
  for file in "${files[@]}"; do
    printf '  %s\n' "$file"
  done
}

build
