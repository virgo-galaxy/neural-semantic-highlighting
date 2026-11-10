<?php

function message(string $name): string {
    return <<<MAIL
Hello {$name},
Your document is ready. 🌌
MAIL;
}

$literal = <<<'TEXT'
The $name variable and "quotes" stay literal.
TEXT;
