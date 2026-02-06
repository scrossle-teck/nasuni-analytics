Describe 'find-missing-admins.ps1' {
    It 'Reports folders missing admin identities' {
        $testRoot = Join-Path $PSScriptRoot '..\..\pester-tmp'
        $runId = 'run-test-pester-missing'
        $tmp = Join-Path $testRoot $runId
        if (Test-Path $tmp) { Remove-Item -Recurse -Force $tmp }
        New-Item -ItemType Directory -Path (Join-Path $tmp 'folderacls') -Force | Out-Null

        $sample = @{ path = '\\nasuni\share\noadmin'; acl = @(
                @{ name = 'Domain Users'; rights = 'Read' }
            ) 
        }
        $sample2 = @{ path = '\\nasuni\share\withadmin'; acl = @(
                @{ name = 'Administrators'; rights = 'FullControl' }
            ) 
        }
        $sample3 = @{ path = '\\nasuni\share\withadmin_read'; acl = @(
                @{ name = 'Administrators'; rights = 'Read' }
            ) 
        }

        $sample | ConvertTo-Json -Depth 20 | Out-File -FilePath (Join-Path $tmp 'folderacls\noadmin.json') -Encoding UTF8
        $sample2 | ConvertTo-Json -Depth 20 | Out-File -FilePath (Join-Path $tmp 'folderacls\withadmin.json') -Encoding UTF8
        $sample3 | ConvertTo-Json -Depth 20 | Out-File -FilePath (Join-Path $tmp 'folderacls\withadmin_read.json') -Encoding UTF8

        $repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $script = Join-Path $repo 'scripts\find-missing-admins.ps1'
        $rules = Join-Path $repo 'scripts\ruleset.json'
        $out = Join-Path $tmp 'missing.csv'
        & $script -RunPath $tmp -OutPath $out -RuleId 'AdminsMissing' -Ruleset $rules

        Test-Path $out | Should -BeTrue
        $rows = Import-Csv $out
        # should report the folder missing admin identities
        ($rows.folder_path -contains '\\nasuni\share\noadmin') | Should -BeTrue
        ($rows.folder_path -contains '\\nasuni\share\withadmin') | Should -BeFalse
        ($rows.folder_path -contains '\\nasuni\share\withadmin_read') | Should -BeTrue
    }
}
