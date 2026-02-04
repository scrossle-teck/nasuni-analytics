$tmp = Join-Path $PSScriptRoot '..\pester-debug'
Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue

# --- Broad perms run ---
$bRun = Join-Path $tmp 'run-broad'
$fa = Join-Path $bRun 'folderacls'
New-Item -ItemType Directory -Path $fa -Force | Out-Null

$sample = @{ path = '\\nasuni\\share\\folder1'; acl = @(@{ sid = 'S-1-5-21-1000'; name = 'Domain Users'; type = 'allow'; mask = 'FullControl'; inherited = $false }) }
$json = $sample | ConvertTo-Json -Depth 5
Set-Content -Path (Join-Path $fa 'sample.json') -Value $json -Encoding UTF8

$script = Join-Path $PSScriptRoot '..\scripts\find-broad-perms.ps1'
Write-Output "Running broad script: $script"
& $script -RunPath $bRun -OutPath (Join-Path $bRun 'broad.csv') -Verbose
Write-Output 'Files (broad run):'
Get-ChildItem -Recurse -Path $bRun | ForEach-Object { Write-Output $_.FullName }
Write-Output '--- show broad.csv if exists ---'
if (Test-Path (Join-Path $bRun 'broad.csv')) { Get-Content (Join-Path $bRun 'broad.csv') | Select-Object -First 40 | ForEach-Object { Write-Output $_ } } else { Write-Output 'broad.csv not created' }

# --- Accessible-by run ---
$arun = Join-Path $tmp 'run-access'
$afa = Join-Path $arun 'folderacls'
New-Item -ItemType Directory -Path $afa -Force | Out-Null
$sample2 = @{ path = '\\nasuni\\share\\folder2'; acl = @(@{ sid = 'S-1-5-21-1000'; name = 'Domain Users'; type = 'allow'; mask = 'FullControl'; inherited = $false }) }
Set-Content -Path (Join-Path $afa 'sample.json') -Value ($sample2 | ConvertTo-Json -Depth 5) -Encoding UTF8

$script2 = Join-Path $PSScriptRoot '..\scripts\find-accessible-by.ps1'
Write-Output "Running access script: $script2"
& $script2 -RunPath $arun -Identity 'Domain Users' -OutPath (Join-Path $arun 'access.csv') -Verbose
Write-Output 'Files (access run):'
Get-ChildItem -Recurse -Path $arun | ForEach-Object { Write-Output $_.FullName }
if (Test-Path (Join-Path $arun 'access.csv')) { Write-Output 'access.csv created'; Get-Content (Join-Path $arun 'access.csv') | Select-Object -First 40 | ForEach-Object { Write-Output $_ } } else { Write-Output 'access.csv not created' }

Write-Output 'Debug run complete.'
