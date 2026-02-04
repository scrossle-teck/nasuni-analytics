param(
    [Parameter(Mandatory = $true)][string]$Path
)

Write-Output "Inspecting: $Path"
$s = Get-Content -Raw -Path $Path
Write-Output "RAW:"; Write-Output $s
$j = $s | ConvertFrom-Json
Write-Output "Properties:"; $j | Get-Member -MemberType *Property | ForEach-Object { Write-Output $_.Name }
Write-Output "Has acl?"; Write-Output ($j.PSObject.Properties.Name -contains 'acl')
Write-Output "ACL count:"; Write-Output ($j.acl.Count)
Write-Output "First ace properties:"; $j.acl[0] | Get-Member -MemberType *Property | ForEach-Object { Write-Output $_.Name }
Write-Output "First ace name:"; Write-Output $j.acl[0].name
