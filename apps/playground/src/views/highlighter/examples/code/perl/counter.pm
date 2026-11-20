package Virgo::Counter;
use strict;
use warnings;

sub new {
    my ($class, $initial) = @_;
    return bless { count => $initial // 0 }, $class;
}

sub increment {
    my ($self) = @_;
    return ++$self->{count};
}

my $counter = Virgo::Counter->new(3);
print $counter->increment(), "\n";
1;
