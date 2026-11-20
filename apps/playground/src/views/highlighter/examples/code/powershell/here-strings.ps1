$name = 'Virgo'
$message = @"
Hello, $name!
The report is ready.
"@

$template = @'
$HOME stays literal here.
"Quoted text" and # notes are part of the string.
'@

Write-Output $message
Write-Output $template
