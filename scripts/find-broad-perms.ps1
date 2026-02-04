<#
.SYNOPSIS
  Find folders where broad groups have elevated permissions.

.DESCRIPTION
  Scans JSON ACL exports under a run folder and reports ACEs matching a set
  of broad identities (default: Domain Users, Everyone, BUILTIN\\Users) where
  the ACE indicates high permissions (heuristic match on 'Full' in mask/rights).

.PARAMETER RunPath
  Path to the run folder containing a `folderacls` directory.

.PARAMETER OutPath
  CSV output path.

.PARAMETER Targets
  Array of identity name patterns to treat as broad groups.

.PARAMETER IncludeInherited
  Include ACEs marked as inherited.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [string]$OutPath = "results/broad-perms.csv",
    [string[]]$Targets = @('Domain Users', 'Everyone', 'BUILTIN\\Users'),
    [string]$Ruleset = (Join-Path $PSScriptRoot 'ruleset.json'),
    [switch]$IncludeInherited
)

Set-StrictMode -Version Latest

# load ACE helpers
. "$PSScriptRoot\ace-utils.ps1"

function Get-FolderAclFiles {
    param([string]$runPath)
    $fa = Join-Path $runPath 'folderacls'
    if (Test-Path $fa) { Get-ChildItem -Path $fa -Filter *.json -File -ErrorAction SilentlyContinue }
    else { Get-ChildItem -Path $runPath -Recurse -Include *.json -File -ErrorAction SilentlyContinue | Where-Object { $_.FullName -match 'folderacls' } }
}

function Find-AclNodes([object]$node) {
    if ($null -eq $node) { return }
    if ($node -is [System.Collections.IDictionary]) {
        foreach ($kv in $node.GetEnumerator()) {
            $k = $kv.Key
            $v = $kv.Value
            if ($k -match '^(acl|acls|aces|aclList)$' -and ($v -is [System.Collections.IEnumerable])) {
                [PSCustomObject]@{Node = $node; AclList = $v }
            }
            else { foreach ($child in Find-AclNodes $v) { $child } }
        }
    }
    elseif ($node -is [System.Collections.IEnumerable] -and -not ($node -is [string])) {
        foreach ($item in $node) { foreach ($child in Find-AclNodes $item) { $child } }
    }
}

function Normalize-Ace($ace) {
    # Accept hashtables, PSCustomObject, and similar as dict-like
    if ($ace -is [System.Collections.IDictionary] -or $ace -is [System.Management.Automation.PSObject]) { return $ace }
    return @{ raw = $ace }
}

$out = [System.Collections.Generic.List[object]]::new()

# Load ruleset if available
$rules = $null
if ($Ruleset -and (Test-Path $Ruleset)) {
    try { $rules = Get-Content -Raw -Path $Ruleset | ConvertFrom-Json -Depth 5 }
    catch { Write-Warning ("Failed to read ruleset {0}: {1}" -f $Ruleset, $_); $rules = $null }
}

foreach ($f in Get-FolderAclFiles -runPath $RunPath) {
    try { $json = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json -Depth 10 }
    catch { Write-Warning "Failed to parse $($f.FullName): $_"; continue }

    Write-Output "Parsed JSON properties: $($json.PSObject.Properties.Name -join ',')"

    # Prefer top-level 'acl' if present (common in exports)
    if ($json.PSObject.Properties.Name -contains 'acl' -and ($json.acl -is [System.Collections.IEnumerable])) {
        Write-Output "Found top-level ACL in $($f.FullName)"
        $node = $json
        $aclList = $json.acl
        $folderPath = $null
        if ($json.PSObject.Properties.Name -contains 'path') { $folderPath = $json.path }
        if (-not $folderPath -and ($json.PSObject.Properties.Name -contains 'folder')) { $folderPath = $json.folder }
        if (-not $folderPath -and ($json.PSObject.Properties.Name -contains 'name')) { $folderPath = $json.name }
        if (-not $folderPath) { $folderPath = $f.FullName }

        foreach ($ace in $aclList) {
            $aceDict = Normalize-Ace $ace
            $aceName = $null
            if ($aceDict.PSObject.Properties.Name -contains 'name') { $aceName = $aceDict.name }
            if (-not $aceName -and ($aceDict.PSObject.Properties.Name -contains 'displayName')) { $aceName = $aceDict.displayName }
            if (-not $aceName -and ($aceDict.PSObject.Properties.Name -contains 'identity')) { $aceName = $aceDict.identity }
            if (-not $aceName -and ($aceDict.PSObject.Properties.Name -contains 'sid')) { $aceName = $aceDict.sid }
            if (-not $aceName) { $aceName = '' }

            $aceSid = ''
            if ($aceDict.PSObject.Properties.Name -contains 'sid') { $aceSid = $aceDict.sid }

            $aceMask = ''
            if ($aceDict.PSObject.Properties.Name -contains 'mask') { $aceMask = $aceDict.mask }
            elseif ($aceDict.PSObject.Properties.Name -contains 'rights') { $aceMask = $aceDict.rights }
            elseif ($aceDict.PSObject.Properties.Name -contains 'permissions') { $aceMask = $aceDict.permissions }
            $aceInherited = $aceDict.inherited -eq $true

            if ($aceInherited -and -not $IncludeInherited) { continue }

            # Determine matches either via ruleset (preferred) or fallback Targets + heuristic
            $matchedRuleIds = @()
            if ($rules -and $rules.rules) {
                foreach ($rule in $rules.rules) {
                    $identityMatched = $false
                    foreach ($pat in $rule.identity_patterns) {
                        if ($aceName -and ($aceName -like "*$pat*")) { $identityMatched = $true; break }
                        if ($aceSid -and ($aceSid -like "*$pat*")) { $identityMatched = $true; break }
                    }
                    if (-not $identityMatched) { continue }

                    $permMatched = $false
                    if ($rule.PSObject.Properties.Name -contains 'perm_match') {
                        try {
                            if (Test-HighPermission $aceMask -and ($aceMask -match $rule.perm_match)) { $permMatched = $true }
                        }
                        catch { }
                    }
                    else {
                        if (Test-HighPermission $aceMask) { $permMatched = $true }
                    }

                    if ($permMatched) { $matchedRuleIds += $rule.id }
                }
            }
            else {
                $targetMatch = $false
                foreach ($t in $Targets) {
                    if ($aceName -and ($aceName -like "*$t*")) { $targetMatch = $true; break }
                    if ($aceSid -and ($aceSid -like "*$t*")) { $targetMatch = $true; break }
                }

                $highPerm = Test-HighPermission $aceMask

                if ($targetMatch -and $highPerm) { $matchedRuleIds += 'fallback' }
            }

            Write-Output "ACE eval: name='$aceName' sid='$aceSid' mask='$aceMask' inherited=$aceInherited matchedRules=$($matchedRuleIds -join ',')"

            if ($matchedRuleIds.Count -gt 0) {
                Write-Output "Matched ACE: $aceName on $folderPath via rules: $($matchedRuleIds -join ',')"
                $out.Add([PSCustomObject]@{
                        source_file   = $f.FullName
                        folder_path   = $folderPath
                        ace_name      = $aceName
                        ace_sid       = $aceSid
                        ace_mask      = $aceMask
                        ace_inherited = $aceInherited
                        matched_rules = ($matchedRuleIds -join ',')
                        ace_raw       = ($ace | ConvertTo-Json -Depth 5 -Compress)
                    })
            }
        }
        continue
    }

    foreach ($nodeInfo in Find-AclNodes $json) {
        $node = $nodeInfo.Node
        $aclList = $nodeInfo.AclList
        # attempt to find folder path
        $folderPath = $null
        foreach ($cand in @('path', 'folder', 'name', 'folderPath', 'folder_path')) {
            if ($node.PSObject.Properties.Name -contains $cand) { $folderPath = $node.$cand; break }
        }
        if (-not $folderPath) { $folderPath = $f.FullName }

        foreach ($ace in $aclList) {
            $aceDict = Normalize-Ace $ace
            $aceName = $aceDict.name -or $aceDict.displayName -or $aceDict.identity -or $aceDict.sid -or ''
            $aceSid = $aceDict.sid -or ''
            $aceMask = $aceDict.mask -or $aceDict.rights -or $aceDict.permissions -or ''
            $aceInherited = $aceDict.inherited -eq $true

            if ($aceInherited -and -not $IncludeInherited) { continue }

            $targetMatch = $false
            foreach ($t in $Targets) {
                if ($aceName -and ($aceName -like "*$t*")) { $targetMatch = $true; break }
                if ($aceSid -and ($aceSid -like "*$t*")) { $targetMatch = $true; break }
            }

            $highPerm = $false
            if ($aceMask -is [string] -and ($aceMask -match '(?i)full|fullcontrol|modify|write')) { $highPerm = $true }
            elseif ($aceMask -is [int] -and ($aceMask -gt 0)) { $highPerm = $true }

            if ($targetMatch -and $highPerm) {
                $out.Add([PSCustomObject]@{
                        source_file   = $f.FullName
                        folder_path   = $folderPath
                        ace_name      = $aceName
                        ace_sid       = $aceSid
                        ace_mask      = $aceMask
                        ace_inherited = $aceInherited
                        ace_raw       = ($ace | ConvertTo-Json -Depth 5 -Compress)
                    })
            }
        }
    }
}

if ($out.Count -eq 0) { Write-Output "No broad permissions found."; exit 0 }

$outDir = Split-Path -Parent $OutPath
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$out | Export-Csv -Path $OutPath -NoTypeInformation -Encoding UTF8
Write-Output "Results written to: $OutPath"
