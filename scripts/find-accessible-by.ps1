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
    [Parameter(Mandatory=$true)][string]$RunPath,
    [Parameter(Mandatory=$true)][string]$Identity,
    [string]$OutPath = "results/accessible-by.csv",
    [switch]$IncludeInherited
)

Set-StrictMode -Version Latest

function Get-FolderAclFiles { param([string]$runPath) $fa = Join-Path $runPath 'folderacls'; if (Test-Path $fa) { Get-ChildItem -Path $fa -Filter *.json -File } else { Get-ChildItem -Path $runPath -Recurse -Include *.json -File | Where-Object { $_.FullName -match 'folderacls' } } }

function Find-AclNodes([object]$node) {
    if ($null -eq $node) { return }
    if ($node -is [System.Collections.IDictionary]) {
        foreach ($kv in $node.GetEnumerator()) {
            $k = $kv.Key; $v = $kv.Value
            if ($k -match '^(acl|acls|aces|aclList)$' -and ($v -is [System.Collections.IEnumerable])) { [PSCustomObject]@{Node=$node; AclList=$v} }
            else { foreach ($child in Find-AclNodes $v) { $child } }
        }
    }
    elseif ($node -is [System.Collections.IEnumerable] -and -not ($node -is [string])) { foreach ($item in $node) { foreach ($child in Find-AclNodes $item) { $child } } }
}

$results = [System.Collections.Generic.List[object]]::new()

foreach ($f in Get-FolderAclFiles -runPath $RunPath) {
    try { $json = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json -Depth 10 }
    catch { Write-Warning "Failed to parse $($f.FullName): $_"; continue }

    foreach ($nodeInfo in Find-AclNodes $json) {
        $node = $nodeInfo.Node; $aclList = $nodeInfo.AclList
        $folderPath = $null
        foreach ($cand in @('path','folder','name','folderPath','folder_path')) { if ($node.PSObject.Properties.Name -contains $cand) { $folderPath = $node.$cand; break } }
        if (-not $folderPath) { $folderPath = $f.FullName }

        foreach ($ace in $aclList) {
            $aceObj = $ace
            $aceName = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.name -or $aceObj.displayName -or $aceObj.identity -or '' } else { '' }
            $aceSid = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.sid -or '' } else { '' }
            $aceInherited = if ($aceObj -is [System.Collections.IDictionary]) { $aceObj.inherited -eq $true } else { $false }
            if ($aceInherited -and -not $IncludeInherited) { continue }

            if (($aceName -and ($aceName -like "*${Identity}*")) -or ($aceSid -and ($aceSid -like "*${Identity}*"))) {
                $results.Add([PSCustomObject]@{
                    source_file = $f.FullName
                    folder_path = $folderPath
                    ace_name = $aceName
                    ace_sid = $aceSid
                    ace_inherited = $aceInherited
                    ace_raw = ($ace | ConvertTo-Json -Depth 5 -Compress)
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
