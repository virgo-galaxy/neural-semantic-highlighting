function Get-Greeting {
    param([string]$Name, [int]$Count = 2)
    for ($i = 0; $i -lt $Count; $i++) {
        Write-Output "Hello, $Name!"
    }
}

Get-Greeting -Name 'Virgo' -Count 3
