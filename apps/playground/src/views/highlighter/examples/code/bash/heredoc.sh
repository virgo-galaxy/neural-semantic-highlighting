#!/usr/bin/env bash

name=Virgo
cat <<EOF
Hello $name!
This is a here document.
EOF

cat <<'LITERAL'
$name and $(date) remain literal text.
LITERAL

cat <<-TABS
	Leading tabs can be stripped.
	TABS

printf '%s\n' "Finished"
