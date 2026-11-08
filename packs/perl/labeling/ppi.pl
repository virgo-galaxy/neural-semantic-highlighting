use strict;
use warnings;
use JSON::PP;
use PPI;
use Scalar::Util qw(refaddr);
binmode STDIN, ':raw';
binmode STDOUT, ':raw';
$| = 1;
my $json = JSON::PP->new->utf8;
while (my $line = <STDIN>) {
    my $result = eval {
        my $request = $json->decode($line);
        my $source = $request->{source};
        my $document = PPI::Document->new(\$source) or die 'PPI rejected source';
        $document->index_locations;
        my %declarations;
        for my $statement (@{$document->find('PPI::Statement::Variable') || []}) {
            $declarations{refaddr($_)} = 1 for $statement->symbols;
        }
        my @tokens;
        for my $token ($document->tokens) {
            push @tokens, {
                class => ref($token), text => $token->content,
                location => $token->location,
                declaration => $declarations{refaddr($token)} ? 1 : 0,
                ($token->isa('PPI::Token::Word') ? (
                    method => $token->method_call ? 1 : 0,
                    builtin => exists $PPI::Singletons::KEYWORDS{$token->content} ? 1 : 0,
                ) : ()),
                ($token->isa('PPI::Token::HereDoc') ? (
                    bodyLines => scalar($token->heredoc), terminator => $token->terminator,
                ) : ()),
            };
        }
        +{tokens => \@tokens, ppiVersion => $PPI::VERSION};
    };
    $result = {error => 'Offline PPI parse failed'} if $@;
    print $json->encode($result), "\n";
}
