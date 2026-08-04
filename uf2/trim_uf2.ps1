<#
Trims a UF2 file down to a given size, keeping only blocks whose target
address falls within [FlashBase, FlashBase + SizeMB). Renumbers BlockNo /
NumBlocks in the kept blocks so the output is a valid, self-consistent UF2.

Usage:
    .\trim_uf2.ps1 -InFile badge_backup.uf2 -OutFile badge_backup_trimmed.uf2 -SizeMB 4
#>
param(
    [string]$InFile   = "badge_backup.uf2",
    [string]$OutFile  = "badge_backup_trimmed.uf2",
    [int]$SizeMB      = 4,
    [uint32]$FlashBase = 0x10000000
)

$BlockSize = 512
$TrimBytes = [uint32]($SizeMB * 1MB)
$FlashEnd  = $FlashBase + $TrimBytes

# [System.IO.File] methods use .NET's Environment.CurrentDirectory, which can
# drift from PowerShell's own working directory ($PWD / Get-Location) - e.g.
# in the VS Code integrated terminal. Resolve against $PWD explicitly so
# relative paths behave the way the prompt suggests they should.
$ResolvedInFile = if ([System.IO.Path]::IsPathRooted($InFile)) { $InFile } else { Join-Path $PWD.Path $InFile }
if (-not (Test-Path -LiteralPath $ResolvedInFile)) {
    throw "Input file not found: $ResolvedInFile"
}
$OutFile = if ([System.IO.Path]::IsPathRooted($OutFile)) { $OutFile } else { Join-Path $PWD.Path $OutFile }

$bytes = [System.IO.File]::ReadAllBytes($ResolvedInFile)
if ($bytes.Length % $BlockSize -ne 0) {
    throw "Input file size is not a multiple of $BlockSize bytes - not a valid UF2 file."
}
$totalBlocks = $bytes.Length / $BlockSize
Write-Host "Read ${ResolvedInFile}: $totalBlocks blocks ($($bytes.Length) bytes)"

$kept = New-Object System.Collections.Generic.List[byte[]]

for ($i = 0; $i -lt $totalBlocks; $i++) {
    $offset = $i * $BlockSize
    $magic0 = [BitConverter]::ToUInt32($bytes, $offset)
    if ($magic0 -ne 0x0A324655) {
        throw "Block $i has bad magic - not a valid UF2 block."
    }
    $targetAddr = [BitConverter]::ToUInt32($bytes, $offset + 12)
    if ($targetAddr -ge $FlashBase -and $targetAddr -lt $FlashEnd) {
        $block = New-Object byte[] $BlockSize
        [Array]::Copy($bytes, $offset, $block, 0, $BlockSize)
        $kept.Add($block)
    }
}

$numKept = $kept.Count
if ($numKept -eq 0) {
    throw "No blocks fell within the requested range - check FlashBase/SizeMB."
}

for ($i = 0; $i -lt $numKept; $i++) {
    [BitConverter]::GetBytes([uint32]$i).CopyTo($kept[$i], 20)        # blockNo
    [BitConverter]::GetBytes([uint32]$numKept).CopyTo($kept[$i], 24)  # numBlocks
}

$outBytes = New-Object byte[] ($numKept * $BlockSize)
for ($i = 0; $i -lt $numKept; $i++) {
    [Array]::Copy($kept[$i], 0, $outBytes, $i * $BlockSize, $BlockSize)
}

[System.IO.File]::WriteAllBytes($OutFile, $outBytes)
Write-Host "Kept $numKept of $totalBlocks blocks -> $OutFile ($($outBytes.Length) bytes)"
