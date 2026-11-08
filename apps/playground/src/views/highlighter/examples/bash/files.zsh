#!/bin/zsh
autoload -Uz colors
colors

typeset -a files
files=(app.ts app.tsx)

for file in $files; do
  print -r -- "${file:t}"
done
