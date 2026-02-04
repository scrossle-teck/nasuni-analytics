<#
.SYNOPSIS
  Orchestrate analytics scripts for a run folder.

.PARAMETER RunPath
  Path to the run folder.

.PARAMETER OutDir
  Directory where per-check outputs will be written.

.PARAMETER Checks
  Comma-separated list of checks to run: BroadPerms, AccessibleBy, Summarize

.PARAMETER Identity
  When running AccessibleBy, the identity to query for.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [string]$OutDir = "results",
    [string[]]$Checks = @('BroadPerms', 'Summarize'),
    [string]$Identity,
    [string]$Ruleset = (Join-Path $PSScriptRoot 'ruleset.json')
)

if (-not (Test-Path $RunPath)) { Throw "RunPath not found: $RunPath" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

# Load ruleset if present
$rules = $null
if ($Ruleset -and (Test-Path $Ruleset)) {
    try { $rules = Get-Content -Raw -Path $Ruleset | ConvertFrom-Json -Depth 5 }
    catch { Write-Warning ("Failed to read ruleset {0}: {1}" -f $Ruleset, $_); $rules = $null }
}

foreach ($c in $Checks) {
    # If check matches a rule id, execute rule-driven flow
    $rule = $null
    if ($rules -and $rules.rules) { $rule = $rules.rules | Where-Object { $_.id -ieq $c } }
    if ($rule) {
        $out = Join-Path $OutDir ($rule.id + '.csv')
        if ($rule.perm_match) {
            # run broad-perms and filter rows for this rule id
            $tmp = Join-Path $OutDir ('tmp-' + $rule.id + '.csv')
            & "$PSScriptRoot\find-broad-perms.ps1" -RunPath $RunPath -OutPath $tmp -Ruleset $Ruleset
            if (Test-Path $tmp) {
                try {
                    Import-Csv $tmp | Where-Object { $_.matched_rules -and ($_.matched_rules -like "*${($rule.id)}*") } | Export-Csv -Path $out -NoTypeInformation -Encoding UTF8
                    Remove-Item -Path $tmp -Force -ErrorAction SilentlyContinue
                }
                catch { Write-Warning ("Failed to filter results for rule {0}: {1}" -f $($rule.id), $_) }
            }
            else { Write-Warning "Expected temporary output not found: $tmp" }
        }
        elseif ($rule.expect_presence) {
            # presence check: search for identities in rule
            & "$PSScriptRoot\find-accessible-by.ps1" -RunPath $RunPath -Identity $rule.id -Ruleset $Ruleset -OutPath $out
        }
        else {
            Write-Warning "Rule $($rule.id) has no actionable type; skipping"
        }
        continue
    }

    switch ($c.ToLower()) {
        'broadperms' {
            $out = Join-Path $OutDir 'broad-perms.csv'
            & "$PSScriptRoot\find-broad-perms.ps1" -RunPath $RunPath -OutPath $out -Ruleset $Ruleset
        }
        'accessibleby' {
            if (-not $Identity) { Write-Warning 'AccessibleBy requires -Identity; skipping'; break }
            $out = Join-Path $OutDir 'accessible-by.csv'
            & "$PSScriptRoot\find-accessible-by.ps1" -RunPath $RunPath -Identity $Identity -OutPath $out -Ruleset $Ruleset
        }
        'summarize' {
            $out = Join-Path $OutDir 'run-summary.csv'
            & "$PSScriptRoot\summarize-run.ps1" -RunPath $RunPath -OutPath $out
        }
        default { Write-Warning "Unknown check: $c" }
    }
}

Write-Output "Run analytics complete. Outputs in: $OutDir"
