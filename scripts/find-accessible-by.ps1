<#
.SYNOPSIS
  List folders accessible by a named identity (account or group) within a run.

.PARAMETER RunPath
  Path to the run folder containing `folderacls`.

.PARAMETER Identity
  Display name or SID to match (case-insensitive, substring match supported).

.PARAMETER OutPath
  CSV output path.

.PARAMETER IncludeInherited
  Include inherited ACEs.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [Parameter(Mandatory = $true)][string]$Identity,
    [string]$OutPath = "results/accessible-by.csv",
    [string]$Ruleset = (Join-Path $PSScriptRoot 'ruleset.json'),
    [switch]$IncludeInherited
)

Set-StrictMode -Version Latest

# load ACE helpers
. "$PSScriptRoot\ace-utils.ps1"

function Get-FolderAclFiles { param([string]$runPath) $fa = Join-Path $runPath 'folderacls'; if (Test-Path $fa) { Get-ChildItem -Path $fa -Filter *.json -File } else { Get-ChildItem -Path $runPath -Recurse -Include *.json -File | Where-Object { $_.FullName -match 'folderacls' } } }

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

# results collection
$results = [System.Collections.Generic.List[object]]::new()

# JSON serialization depth for raw ACE output
$JsonDepth = 20

# Load ruleset if provided (allows using a rule id as the -Identity parameter)
$rules = $null
if ($Ruleset -and (Test-Path $Ruleset)) {
    try { $rules = Get-Content -Raw -Path $Ruleset | ConvertFrom-Json -Depth $JsonDepth }
    catch { Write-Warning (("Failed to read ruleset {0}: {1}") -f $Ruleset, $_); $rules = $null }
}

# load top-level admin identities from ruleset (if present)
$globalAdminIdentities = @()
if ($rules -and $rules.admin_identities) { $globalAdminIdentities = $rules.admin_identities }

foreach ($f in Get-FolderAclFiles -runPath $RunPath) {
    try { $json = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json -Depth $JsonDepth }
    catch { Write-Warning "Failed to parse $($f.FullName): $_"; continue }

    Write-Output "Parsed JSON properties: $($json.PSObject.Properties.Name -join ',')"

    # Prefer top-level 'acl' if present
    if ($json.PSObject.Properties.Name -contains 'acl' -and ($json.acl -is [System.Collections.IEnumerable])) {
        Write-Output "Found top-level ACL in $($f.FullName)"
        $aclList = $json.acl
        $folderPath = $null
        if ($json.PSObject.Properties.Name -contains 'path') { $folderPath = $json.path }
        if (-not $folderPath -and ($json.PSObject.Properties.Name -contains 'folder')) { $folderPath = $json.folder }
        if (-not $folderPath -and ($json.PSObject.Properties.Name -contains 'name')) { $folderPath = $json.name }
        if (-not $folderPath) { $folderPath = $f.FullName }

        foreach ($ace in $aclList) {
            $aceObj = $ace
            $aceName = ''
            if ($aceObj -is [System.Management.Automation.PSObject] -or $aceObj -is [System.Collections.IDictionary]) {
                if ($aceObj.PSObject.Properties.Name -contains 'name') { $aceName = $aceObj.name }
                if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'displayName')) { $aceName = $aceObj.displayName }
                if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'identity')) { $aceName = $aceObj.identity }
                if (-not $aceName -and ($aceObj.PSObject.Properties.Name -contains 'sid')) { $aceName = $aceObj.sid }
            }

            $aceSid = ''
            if ($aceObj -is [System.Management.Automation.PSObject] -or $aceObj -is [System.Collections.IDictionary]) {
                if ($aceObj.PSObject.Properties.Name -contains 'sid') { $aceSid = $aceObj.sid }
            }
            $aceInherited = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.inherited -eq $true } else { $false }
            if ($aceInherited -and -not $IncludeInherited) { continue }

            # Determine identity patterns: if Identity matches a rule id, use its identity_patterns or global admin list
            $identityPatterns = @()
            if ($rules -and $rules.rules) {
                $matchedRule = $rules.rules | Where-Object { $_.id -ieq $Identity }
                if ($matchedRule) {
                    if ($matchedRule.PSObject.Properties.Name -contains 'match_admin_identities' -and $matchedRule.match_admin_identities) {
                        if ($globalAdminIdentities) { $identityPatterns = $globalAdminIdentities }
                    }
                    if ($identityPatterns.Count -eq 0 -and $matchedRule.PSObject.Properties.Name -contains 'identity_patterns') { $identityPatterns = @($matchedRule.identity_patterns) }
                }
            }
            if ($identityPatterns.Count -eq 0) { $identityPatterns = @($Identity) }

            $matched = $false
            foreach ($pat in $identityPatterns) {
                if ($aceName -and ($aceName -like "*$pat*")) { $matched = $true; break }
                if ($aceSid -and ($aceSid -like "*$pat*")) { $matched = $true; break }
            }

            if ($matched) {
                Write-Output "Matched identity ACE: $aceName on $folderPath"
                $results.Add([PSCustomObject]@{
                        source_file   = $f.FullName
                        folder_path   = $folderPath
                        ace_name      = $aceName
                        ace_sid       = $aceSid
                        ace_inherited = $aceInherited
                        ace_raw       = ($ace | ConvertTo-Json -Depth $JsonDepth -Compress)
                    })
            }
        }
        continue
    }

    foreach ($nodeInfo in Find-AclNodes $json) {
        $node = $nodeInfo.Node; $aclList = $nodeInfo.AclList
        $folderPath = $null
        foreach ($cand in @('path', 'folder', 'name', 'folderPath', 'folder_path')) { if ($node.PSObject.Properties.Name -contains $cand) { $folderPath = $node.$cand; break } }
        if (-not $folderPath) { $folderPath = $f.FullName }

        foreach ($ace in $aclList) {
            $aceObj = $ace
            $aceName = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.name -or $aceObj.displayName -or $aceObj.identity -or '' } else { '' }
            $aceSid = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.sid -or '' } else { '' }
            $aceInherited = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.inherited -eq $true } else { $false }
            if ($aceInherited -and -not $IncludeInherited) { continue }

            # Determine identity patterns: support rule ids and admin list
            $identityPatterns = @()
            if ($rules -and $rules.rules) {
                $matchedRule = $rules.rules | Where-Object { $_.id -ieq $Identity }
                if ($matchedRule) {
                    if ($matchedRule.PSObject.Properties.Name -contains 'match_admin_identities' -and $matchedRule.match_admin_identities) {
                        if ($globalAdminIdentities) { $identityPatterns = $globalAdminIdentities }
                    }
                    if ($identityPatterns.Count -eq 0 -and $matchedRule.PSObject.Properties.Name -contains 'identity_patterns') { $identityPatterns = @($matchedRule.identity_patterns) }
                }
            }
            if ($identityPatterns.Count -eq 0) { $identityPatterns = @($Identity) }

            $matched = $false
            foreach ($pat in $identityPatterns) {
                if ($aceName -and ($aceName -like "*$pat*")) { $matched = $true; break }
                if ($aceSid -and ($aceSid -like "*$pat*")) { $matched = $true; break }
            }

            if ($matched) {
                $results.Add([PSCustomObject]@{
                        source_file   = $f.FullName
                        folder_path   = $folderPath
                        ace_name      = $aceName
                        ace_sid       = $aceSid
                        ace_inherited = $aceInherited
                        ace_raw       = ($ace | ConvertTo-Json -Depth $JsonDepth -Compress)
                    })
            }
        }
    }
}

if ($results.Count -eq 0) { Write-Output "No matches for identity: $Identity"; exit 0 }

$outDir = Split-Path -Parent $OutPath
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$results | Export-Csv -Path $OutPath -NoTypeInformation -Encoding UTF8
Write-Output "Results written to: $OutPath"
