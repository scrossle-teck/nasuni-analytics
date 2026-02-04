Describe 'find-accessible-by.ps1' {
    It 'Finds ACEs for supplied identity and writes CSV' {
        $testRoot = Join-Path $PSScriptRoot '..\..\pester-tmp'
        $runId = 'run-test-pester-access'
        $runPath = Join-Path $testRoot $runId
        $folderacls = Join-Path $runPath 'folderacls'
        New-Item -ItemType Directory -Path $folderacls -Force | Out-Null

        $sample = @{ path = '\\nasuni\share\folder2'; acl = @(
                @{ sid = 'S-1-5-21-3000'; name = 'SomeUser'; type = 'allow'; mask = 'Read'; inherited = $false },
                @{ sid = 'S-1-5-21-1000'; name = 'Domain Users'; type = 'allow'; mask = 'FullControl'; inherited = $false }
            ) 
        }

        $json = $sample | ConvertTo-Json -Depth 5
        $sampleFile = Join-Path $folderacls 'sample.json'
        Set-Content -Path $sampleFile -Value $json -Encoding UTF8

        $repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')
        $script = Join-Path $repo 'scripts\find-accessible-by.ps1'
        $out = Join-Path $runPath 'accessible-by.csv'

        & $script -RunPath $runPath -Identity 'Domain Users' -OutPath $out

        Test-Path $out | Should -BeTrue
        $rows = Import-Csv $out
        $rows.Count | Should -BeGreaterThan 0
        ($rows | Where-Object { $_.ace_name -like '*Domain Users*' }).Count | Should -BeGreaterThan 0

        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
