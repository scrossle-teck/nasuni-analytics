Describe 'find-broad-perms.ps1' {
    It 'Detects Domain Users FullControl ACEs and writes CSV' {
        $testRoot = Join-Path $PSScriptRoot '..\..\pester-tmp'
        $runId = 'run-test-pester-broad'
        $runPath = Join-Path $testRoot $runId
        $folderacls = Join-Path $runPath 'folderacls'
        New-Item -ItemType Directory -Path $folderacls -Force | Out-Null

        $sample = @{ path = '\\nasuni\share\folder1'; acl = @(
                @{ sid = 'S-1-5-21-1000'; name = 'Domain Users'; type = 'allow'; mask = 'FullControl'; inherited = $false },
                @{ sid = 'S-1-5-21-2000'; name = 'Admins'; type = 'allow'; mask = 'Read'; inherited = $false }
            ) 
        }

        $json = $sample | ConvertTo-Json -Depth 20
        $sampleFile = Join-Path $folderacls 'sample.json'
        Set-Content -Path $sampleFile -Value $json -Encoding UTF8

        $repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')
        $script = Join-Path $repo 'scripts\find-broad-perms.ps1'
        $out = Join-Path $runPath 'broad-perms.csv'

        & $script -RunPath $runPath -OutPath $out

        Test-Path $out | Should -BeTrue
        $rows = Import-Csv $out
        $rows.Count | Should -BeGreaterThan 0
        ($rows | Where-Object { $_.ace_name -like '*Domain Users*' }).Count | Should -BeGreaterThan 0

        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
