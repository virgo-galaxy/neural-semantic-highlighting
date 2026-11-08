{
    for (i = 1; i <= NF; i++) {
        word = tolower($i)
        if (word ~ /^[[:alpha:]]+$/)
            counts[word]++
    }
}

END {
    for (word in counts)
        if (counts[word] > 1)
            print word, counts[word]
}
