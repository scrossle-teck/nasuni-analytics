param(
    [Parameter(Mandatory = $true)][string]$Mask
)
. "$PSScriptRoot\ace-utils.ps1"
Write-Output (Test-HighPermission $Mask)
