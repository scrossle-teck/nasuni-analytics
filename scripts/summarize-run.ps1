<#
.SYNOPSIS
  Produce a small CSV summary for a run folder: file counts, folder counts, ACE counts, unique SIDs.

.PARAMETER RunPath
  Path to the run folder.

.PARAMETER OutPath
  Path to write the CSV summary.
#>
param(
    [Parameter(Mandatory = $true)][string]$RunPath,
    [string]$OutPath = "results/run-summary.csv"
)

Set-StrictMode -Version Latest


function Get-FolderAclFiles { param([string]$runPath) $fa = Join-Path $runPath 'folderacls'; if (Test-Path $fa) { Get-ChildItem -Path $fa -Filter *.json -File } else { Get-ChildItem -Path $runPath -Recurse -Include *.json -File | Where-Object { $_.FullName -match 'folderacls' } } }

$JsonDepth = 20

$totalFiles = 0; $totalAces = 0; $uniqueFolders = [System.Collections.Generic.HashSet[string]]::new(); $uniqueSids = [System.Collections.Generic.HashSet[string]]::new()

foreach ($f in Get-FolderAclFiles -runPath $RunPath) {
    $totalFiles++
    try { $json = Get-Content -Raw -Path $f.FullName | ConvertFrom-Json -Depth $JsonDepth }
    catch { Write-Warning "Failed to parse $($f.FullName): $_"; continue }

    # simple traversal to find ACL lists
    $nodes = (ConvertTo-Json $json -Depth 20) | Out-Null
    # reuse earlier heuristic by searching for lists under likely keys
    $text = Get-Content -Raw -Path $f.FullName
    $acesHere = 0
    # count occurrences of "sid" in file as proxy for ACE count
    $acesHere = ([regex]::Matches($text, '"sid"', 'IgnoreCase')).Count
    $totalAces += $acesHere

    # attempt to extract folder path strings
    try {
        $parsed = $json
        if ($parsed -is [System.Collections.IDictionary]) {
            foreach ($cand in @('UncPath', 'SharePath', 'ShareName', 'VolumeName', 'path', 'folder', 'name', 'folderPath', 'folder_path')) { if ($parsed.PSObject.Properties.Name -contains $cand) { $uniqueFolders.Add([string]$parsed.$cand) | Out-Null } }
        }
    }
    catch { }

    # collect sids roughly
    $sidMatches = [regex]::Matches($text, '"sid"\s*:\s*"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    foreach ($s in $sidMatches) { $uniqueSids.Add($s) | Out-Null }
}

$summary = [PSCustomObject]@{
    run                   = (Split-Path -Leaf $RunPath)
    files_processed       = $totalFiles
    total_aces_approx     = $totalAces
    unique_folders_approx = $uniqueFolders.Count
    unique_sids           = $uniqueSids.Count
}

$outDir = Split-Path -Parent $OutPath
if ($outDir -and -not (Test-Path $outDir)) { New-Item -ItemType Directory -Path $outDir -Force | Out-Null }
$summary | Export-Csv -Path $OutPath -NoTypeInformation -Encoding UTF8
Write-Output "Summary written to: $OutPath"
