function normalize(text) {
    gsub(/^[[:space:]]+|[[:space:]]+$/, "", text)
    gsub(/[[:space:]]+/, "-", text)
    return tolower(text)
}

NF && $0 !~ /^#/ {
    print NR, normalize($0)
}
