my $literal = <<~'LITERAL';
    $name and ${value} stay literal here.
    LITERAL

print $literal;
