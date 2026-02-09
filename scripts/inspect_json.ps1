param(
    [Parameter(Mandatory = $true)][string]$Path
)

$JsonDepth = 20

Write-Output "Inspecting: $Path"
$s = Get-Content -Raw -Path $Path
Write-Output "RAW:"; Write-Output $s
$j = $s | ConvertFrom-Json -Depth $JsonDepth
Write-Output "Properties:"; $j | Get-Member -MemberType *Property | ForEach-Object { Write-Output $_.Name }
Write-Output "Has acl?"; Write-Output (($j.PSObject.Properties.Name -contains 'acl') -or ($j.PSObject.Properties.Name -contains 'Access'))
Write-Output "ACL count:"; if ($j.PSObject.Properties.Name -contains 'acl') { Write-Output ($j.acl.Count) } elseif ($j.PSObject.Properties.Name -contains 'Access') { Write-Output ($j.Access.Count) } else { Write-Output 0 }
if ($j.PSObject.Properties.Name -contains 'acl') { Write-Output "First ace properties:"; $j.acl[0] | Get-Member -MemberType *Property | ForEach-Object { Write-Output $_.Name }; Write-Output "First ace name:"; Write-Output $j.acl[0].name }
elseif ($j.PSObject.Properties.Name -contains 'Access') { Write-Output "First ace properties:"; $j.Access[0] | Get-Member -MemberType *Property | ForEach-Object { Write-Output $_.Name }; Write-Output "First ace name:"; Write-Output $j.Access[0].Identity -or $j.Access[0].name }
