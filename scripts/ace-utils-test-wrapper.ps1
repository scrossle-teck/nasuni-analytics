<#
Simple wrapper to run ace-utils functions in a separate process and emit JSON results.
Used by Pester to avoid dot-sourcing discovery issues.
#>
param()
. "$PSScriptRoot\ace-utils.ps1"

$cases = @{
    'full_str'    = @(Test-HighPermission 'FullControl')
    'modify_str'  = @(Test-HighPermission 'modify')
    'read_str'    = @(Test-HighPermission 'read')
    'hex_generic' = @(Test-HighPermission '0x10000000')
    'hex_small'   = @(Test-HighPermission '0x2')
    'zero'        = @(Test-HighPermission 0)
}

($cases | ConvertTo-Json -Depth 5) | Write-Output
