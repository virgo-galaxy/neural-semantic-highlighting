#!/usr/bin/env bash

function greet() {
  printf 'Hello, %s!\n' "$1"
}

function report {
  local count=${1:-3}
  printf 'Processed %s files\n' "$count"
}

greet Virgo
report 5
