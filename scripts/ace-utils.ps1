function Convert-ToIntMask {
    param([Parameter(Mandatory = $true)][object]$Mask)
    if ($null -eq $Mask) { return 0 }
    if ($Mask -is [int] -or $Mask -is [long]) { return [int64]$Mask }
    $s = [string]$Mask
    if ($s -match '^0x') {
        try { return [Convert]::ToInt64($s, 16) } catch { return 0 }
    }
    $i = 0
    if ([Int64]::TryParse($s, [ref]$i)) { return $i }
    return 0
}

function Test-HighPermission {
    param([object]$Mask)
    # String-based heuristics
    if ($Mask -is [string]) {
        if ($Mask -match '(?i)full|fullcontrol|modify|write') { return $true }
        # numeric string (hex or decimal)
    }

    $val = Convert-ToIntMask $Mask
    if ($val -eq 0) { return $false }

    # Generic access masks (Windows GENERIC_*) and common write bits
    $bits = @(0x10000000, 0x40000000, 0x80000000, 0x00000002, 0x00000004, 0x00000010, 0x00000020)
    foreach ($b in $bits) { if (($val -band $b) -ne 0) { return $true } }
    return $false
}

function Normalize-MaskString {
    param([object]$Mask)
    if ($null -eq $Mask) { return '' }
    if ($Mask -is [int] -or $Mask -is [long]) { return ('0x{0:X}' -f (Convert-ToIntMask $Mask)) }
    $s = [string]$Mask
    if ($s -match '^0x') { return $s.ToLower() }
    return $s
}

# exported helpers are available when dot-sourced
