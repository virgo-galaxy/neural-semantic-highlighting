$records = @(
    [pscustomobject]@{ Name = 'Alpha'; Score = 92 },
    [pscustomobject]@{ Name = 'Beta'; Score = 78 }
)

foreach ($record in $records) {
    if ($record.Score -ge 80) {
        Write-Output $record.Name
    }
}
