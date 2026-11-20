use strict;
use warnings;
use feature 'say';

my @records = (
    { name => 'Virgo', score => 12 },
    { name => 'Preview', score => 8 },
);

for my $record (@records) {
    next unless $record->{score} >= 10;
    say $record->{name}, ': ', $record->{score};
}
