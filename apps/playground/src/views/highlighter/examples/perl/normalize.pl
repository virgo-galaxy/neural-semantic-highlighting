use strict;
use warnings;

sub normalize {
    my ($name) = @_;
    $name =~ s/^\s+|\s+$//g;
    $name =~ s/\s+/-/g;
    return lc $name;
}

my @names = ('Virgo Design', 'Cloud Docs');
my @slugs = map { normalize($_) } @names;
print join("\n", @slugs), "\n";
