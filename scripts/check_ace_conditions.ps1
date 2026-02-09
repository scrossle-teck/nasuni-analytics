param(
    [Parameter(Mandatory = $true)][string]$Path
)

$JsonDepth = 20

$s = Get-Content -Raw -Path $Path
$j = $s | ConvertFrom-Json -Depth $JsonDepth
# support either top-level 'acl' or 'Access'
if ($j.PSObject.Properties.Name -contains 'acl') { $ace = $j.acl[0] }
elseif ($j.PSObject.Properties.Name -contains 'Access') { $ace = $j.Access[0] }
else { Write-Warning 'No ACL list found'; exit 1 }

Write-Output "aceName: $($ace.name -or $ace.identity)"
Write-Output "aceSid: $($ace.sid)"
Write-Output "aceMask: $($ace.mask -or $ace.rights)"
Write-Output "aceInherited: $($ace.inherited -or $ace.IsInherited -or $ace.isInherited)"

$targets = @('Domain Users', 'Everyone', 'BUILTIN\\Users')
foreach ($t in $targets) {
    $match = ($ace.name -and ($ace.name -like "*$t*")) -or ($ace.sid -and ($ace.sid -like "*$t*"))
    Write-Output "Target '$t' match: $match"
}

$highPerm = $false
if ($ace.mask -is [string] -and ($ace.mask -match '(?i)full|fullcontrol|modify|write')) { $highPerm = $true }
elseif ($ace.mask -is [int] -and ($ace.mask -gt 0)) { $highPerm = $true }
Write-Output "HighPerm: $highPerm"
