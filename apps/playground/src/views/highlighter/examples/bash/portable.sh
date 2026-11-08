#!/bin/sh
source_dir=${1:-assets}
target_dir=${2:-public}

mkdir -p "$target_dir"
for file in "$source_dir"/*; do
  if [ -f "$file" ]; then
    cp "$file" "$target_dir/"
  fi
done
