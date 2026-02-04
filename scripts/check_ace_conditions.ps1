param(
    [Parameter(Mandatory = $true)][string]$Path
)

$s = Get-Content -Raw -Path $Path
$j = $s | ConvertFrom-Json
$ace = $j.acl[0]
Write-Output "aceName: $($ace.name)"
Write-Output "aceSid: $($ace.sid)"
Write-Output "aceMask: $($ace.mask)"
Write-Output "aceInherited: $($ace.inherited)"

$targets = @('Domain Users', 'Everyone', 'BUILTIN\\Users')
foreach ($t in $targets) {
    $match = ($ace.name -and ($ace.name -like "*$t*")) -or ($ace.sid -and ($ace.sid -like "*$t*"))
    Write-Output "Target '$t' match: $match"
}

$highPerm = $false
if ($ace.mask -is [string] -and ($ace.mask -match '(?i)full|fullcontrol|modify|write')) { $highPerm = $true }
elseif ($ace.mask -is [int] -and ($ace.mask -gt 0)) { $highPerm = $true }
Write-Output "HighPerm: $highPerm"
