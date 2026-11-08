$options = @{ Path = './src'; Recurse = $true }

Get-ChildItem @options |
    Where-Object { $_.Extension -eq '.ts' } |
    Sort-Object Length -Descending |
    Select-Object -First 8 Name, Length
