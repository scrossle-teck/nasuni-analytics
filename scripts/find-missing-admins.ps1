<#
.SYNOPSIS
  Report folders missing configured admin identities.

.DESCRIPTION
  Uses a ruleset entry (e.g., `AdminsMissing`) that declares `identity_patterns` and
  treats the rule as an expectation: any folder without at least one matching ACE
  will be reported.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [string]$OutPath = "results/missing-admins.csv",
    [string]$RuleId = 'AdminsMissing',
    [string]$Ruleset = (Join-Path $PSScriptRoot 'ruleset.json'),
    [switch]$IncludeInherited
)

Set-StrictMode -Version Latest
. "$PSScriptRoot\ace-utils.ps1"

function Get-FolderAclFiles { param([string]$runPath) $fa = Join-Path $runPath 'folderacls'; if (Test-Path $fa) { Get-ChildItem -Path $fa -Filter *.json -File -ErrorAction SilentlyContinue } else { Get-ChildItem -Path $runPath -Recurse -Include *.json -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'folderacls' } } }

function Find-AclNodes([object]$node) {
    if ($null -eq $node) { return }
    if ($node -is [System.Collections.IDictionary]) {
        foreach ($kv in $node.GetEnumerator()) {
            $k = $kv.Key; $v = $kv.Value
            if ($k -match '^(acl|acls|aces|aclList)$' -and ($v -is [System.Collections.IEnumerable])) { [PSCustomObject]@{Node = $node; AclList = $v } }
            else { foreach ($child in Find-AclNodes $v) { $child } }
        }
    }
    elseif ($node -is [System.Collections.IEnumerable] -and -not ($node -is [string])) { foreach ($item in $node) { foreach ($child in Find-AclNodes $item) { $child } } }
}

# load ruleset and find rule
$rule = $null
if ($Ruleset -and (Test-Path $Ruleset)) {
    try { $rs = Get-Content -Raw -Path $Ruleset | ConvertFrom-Json -Depth 5 }
    catch { Write-Warning ("Failed to read ruleset {0}: {1}" -f $Ruleset, $_); $rs = $null }
    if ($rs -and $rs.rules) { $rule = $rs.rules | Where-Object { $_.id -ieq $RuleId } }
}

if (-not $rule) { Throw "Rule not found in ruleset: $RuleId" }

$out = [System.Collections.Generic.List[object]]::new()

foreach ($f in Get-FolderAclFiles -runPath $RunPath) {
    try { $json = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json -Depth 10 }
    catch { Write-Warning "Failed to parse $($f.FullName): $_"; continue }

    # find ACL list(s)
    $aclLists = @()
    if ($json.PSObject.Properties.Name -contains 'acl' -and ($json.acl -is [System.Collections.IEnumerable])) { $aclLists += , @{List = $json.acl; Node = $json } }
    foreach ($nodeInfo in (Find-AclNodes $json)) { $aclLists += , @{List = $nodeInfo.AclList; Node = $nodeInfo.Node } }

    foreach ($entry in $aclLists) {
        $aclList = $entry.List; $node = $entry.Node
        # deduce folder path
        $folderPath = $null
        foreach ($cand in @('path', 'folder', 'name', 'folderPath', 'folder_path')) { if ($node.PSObject.Properties.Name -contains $cand) { $folderPath = $node.$cand; break } }
        if (-not $folderPath) { $folderPath = $f.FullName }

        $found = @()
        foreach ($ace in $aclList) {
            $aceObj = if ($ace -is [System.Collections.IDictionary] -or $ace -is [System.Management.Automation.PSObject]) { $ace } else { $null }
            if (-not $aceObj) { continue }

            $aceName = ''
            if ($aceObj.PSObject.Properties.Name -contains 'name') { $aceName = $aceObj.name }
            if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'displayName')) { $aceName = $aceObj.displayName }
            if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'identity')) { $aceName = $aceObj.identity }
            if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'sid')) { $aceName = $aceObj.sid }

            $aceSid = ''
            if ($aceObj.PSObject.Properties.Name -contains 'sid') { $aceSid = $aceObj.sid }

            $aceMask = ''
            if ($aceObj.PSObject.Properties.Name -contains 'mask') { $aceMask = $aceObj.mask }
            elseif ($aceObj.PSObject.Properties.Name -contains 'rights') { $aceMask = $aceObj.rights }

            if ($aceObj.PSObject.Properties.Name -contains 'inherited') { $aceInherited = $aceObj.inherited -eq $true } else { $aceInherited = $false }
            if ($aceInherited -and -not $IncludeInherited) { continue }

            # check identity patterns and required permissions
            foreach ($pat in $rule.identity_patterns) {
                if ($aceName -and ($aceName -like "*${pat}*")) {
                    # determine whether ACE meets permission requirement
                    $permOk = $false
                    if ($rule.PSObject.Properties.Name -contains 'perm_match') {
                        try { if ($aceMask -and ($aceMask -match $rule.perm_match)) { $permOk = $true } } catch { }
                    }
                    else {
                        # fallback to heuristics
                        . "$PSScriptRoot\ace-utils.ps1"
                        if (Test-HighPermission $aceMask) { $permOk = $true }
                    }
                    if ($permOk) { $found += $aceName }
                    break
                }
                if ($aceSid -and ($aceSid -like "*${pat}*")) {
                    $permOk = $false
                    if ($rule.PSObject.Properties.Name -contains 'perm_match') {
                        try { if ($aceMask -and ($aceMask -match $rule.perm_match)) { $permOk = $true } } catch { }
                    }
                    else {
                        . "$PSScriptRoot\ace-utils.ps1"
                        if (Test-HighPermission $aceMask) { $permOk = $true }
                    }
                    if ($permOk) { $found += $aceSid }
                    break
                }
            }
        }

        if ($found.Count -eq 0) {
            $out.Add([PSCustomObject]@{
                    source_file         = $f.FullName
                    folder_path         = $folderPath
                    missing_rule        = $rule.id
                    expected_identities = ($rule.identity_patterns -join ',')
                    found_identities    = ''
                })
        }
    }
}

if ($out.Count -eq 0) { Write-Output "No missing admins found."; exit 0 }

$outDir = Split-Path -Parent $OutPath
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$out | Export-Csv -Path $OutPath -NoTypeInformation -Encoding UTF8
Write-Output "Results written to: $OutPath"
