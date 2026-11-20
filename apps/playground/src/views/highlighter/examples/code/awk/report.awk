BEGIN {
    FS = ","
    OFS = "\t"
}

NR == 1 { next }
$3 >= 10 {
    totals[$1] += $3
    records++
}

END {
    for (name in totals)
        printf "%s\t%.2f\n", name, totals[name]
    print "Processed", records, "records"
}
