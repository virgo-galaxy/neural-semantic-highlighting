BEGINFILE { matched = 0 }

/ready|complete/ {
    matched++
    print FILENAME, FNR, $0
}

ENDFILE {
    printf "%s: %d matches\n", FILENAME, matched
}
