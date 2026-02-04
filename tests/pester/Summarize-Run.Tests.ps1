Describe 'summarize-run.ps1' {
    It 'Produces run summary CSV with run id' {
        $testRoot = Join-Path $PSScriptRoot '..\..\pester-tmp'
        $runId = 'run-test-pester-summary'
        $runPath = Join-Path $testRoot $runId
        $folderacls = Join-Path $runPath 'folderacls'
        New-Item -ItemType Directory -Path $folderacls -Force | Out-Null

        $sample = @{ path='\\nasuni\share\folder3'; acl=@(
            @{ sid='S-1-5-21-4000'; name='UserA'; type='allow'; mask='Read'; inherited=$false }
        ) }

        $json = $sample | ConvertTo-Json -Depth 5
        $sampleFile = Join-Path $folderacls 'sample.json'
        Set-Content -Path $sampleFile -Value $json -Encoding UTF8

        $repo = Resolve-Path (Join-Path $PSScriptRoot '..\..')
        $script = Join-Path $repo 'scripts\summarize-run.ps1'
        $out = Join-Path $runPath 'run-summary.csv'

        & $script -RunPath $runPath -OutPath $out

        Test-Path $out | Should -BeTrue
        $rows = Import-Csv $out
        $rows.Count | Should -BeGreaterThan 0
        ($rows[0].run) | Should -Be $runId

        Remove-Item -LiteralPath $testRoot -Recurse -Force
    }
}
