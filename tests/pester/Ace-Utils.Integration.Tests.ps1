Describe 'ace-utils (integration)' {
    It 'Test-HighPermission wrapper returns expected results' {
        $repo = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
        $wrapper = Join-Path $repo 'scripts\ace-utils-test-wrapper.ps1'
        $json = & $wrapper | Out-String
        $data = $json | ConvertFrom-Json

        $data.full_str | Should -BeTrue
        $data.modify_str | Should -BeTrue
        $data.read_str | Should -BeFalse
        $data.hex_generic | Should -BeTrue
        $data.hex_small | Should -BeTrue
        $data.zero | Should -BeFalse
    }
}
