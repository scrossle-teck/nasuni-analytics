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
    [string]$Ruleset = (Join-Path $PSScriptRoot 'ruleset.json'),
    [string]$Python = '',
    [string]$MinSeverity = '',
    [switch]$SeveritySplit
)

if (-not (Test-Path $RunPath)) { Throw "RunPath not found: $RunPath" }
if (-not (Test-Path $OutDir)) { New-Item -ItemType Directory -Path $OutDir -Force | Out-Null }

# Load ruleset if present
$rules = $null
$JsonDepth = 20
if ($Ruleset -and (Test-Path $Ruleset)) {
    try { $rules = Get-Content -Raw -Path $Ruleset | ConvertFrom-Json -Depth $JsonDepth }
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

# After rule-driven checks, also run the Python rule engine (if Parquet exists) to produce a consolidated rule_matches CSV
$runName = Split-Path -Leaf $RunPath
$repoRoot = Resolve-Path (Join-Path $PSScriptRoot '..')
$parquetDir = Join-Path $repoRoot (Join-Path 'out' (Join-Path 'parquet' $runName))
$ruleMatchesOut = Join-Path $OutDir 'rule_matches.csv'
if (Test-Path $parquetDir) {
    # determine python executable: prefer provided -Python, then .venv, then system python
    $pythonExe = $Python
    if (-not $pythonExe -or $pythonExe -eq '') {
        $venvWin = Join-Path $repoRoot '.venv\Scripts\python.exe'
        $venvNix = Join-Path $repoRoot '.venv/bin/python'
        if (Test-Path $venvWin) { $pythonExe = $venvWin }
        elseif (Test-Path $venvNix) { $pythonExe = $venvNix }
        else { $pythonExe = 'python' }
    }

    Write-Output "Invoking apply_rules with python: $pythonExe"
    try {
        $pyArgs = @("${PSScriptRoot}\apply_rules.py", "--run", $parquetDir, "--rules", $Ruleset, "--out", $ruleMatchesOut)
        if ($MinSeverity -and $MinSeverity -ne '') { $pyArgs += @("--min-severity", $MinSeverity) }
        & $pythonExe @pyArgs
        $exit = $LASTEXITCODE
        if ($exit -ne 0) {
            Write-Error "apply_rules.py exited with code $exit"
            Exit $exit
        }
        Write-Output "Rule matches written to: $ruleMatchesOut"
    }
    catch {
        Write-Error ("Failed to run apply_rules.py: {0}" -f $_)
        Exit 2
    }
}
else {
    Write-Warning "Parquet directory not found; skipping apply_rules invocation: $parquetDir"
}

# Optionally split matches by severity into separate CSVs
if ($SeveritySplit -and (Test-Path $ruleMatchesOut)) {
    try {
        $rows = Import-Csv $ruleMatchesOut
        $groups = $rows | Group-Object -Property severity
        foreach ($g in $groups) {
            $sev = $g.Name
            $file = Join-Path $OutDir ("rule_matches_{0}.csv" -f $sev)
            $g.Group | Export-Csv -Path $file -NoTypeInformation -Encoding UTF8
            Write-Output "Wrote severity split: $file"
        }
    }
    catch {
        Write-Warning ("Failed to split rule_matches by severity: {0}" -f $_)
    }
}

Write-Output "Run analytics complete. Outputs in: $OutDir"
