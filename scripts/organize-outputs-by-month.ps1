<#
.SYNOPSIS
    raw/obsidian/outputs/ 직속 문서를 생성월(YYYYMM) 폴더로 정리한다.

.DESCRIPTION
    - 기존 월별 폴더(YYYYMM) 및 그 하위의 attachments/는 건드리지 않는다.
    - 직속 파일만 대상으로 한다.
    - 날짜 우선순위: frontmatter `created:` -> `updated:` -> 파일 LastWriteTime
    - 대상 폴더 (예: 202605/)가 없으면 자동 생성한다.

.PARAMETER Path
    outputs 루트 경로. 생략 시 스크립트 위치 기준 ../raw/obsidian/outputs 를 사용 (양 OS 호환).

.PARAMETER WhatIf
    실제 이동 없이 계획만 출력.

.EXAMPLE
    pwsh ./scripts/organize-outputs-by-month.ps1 -WhatIf
    pwsh ./scripts/organize-outputs-by-month.ps1
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Path
)

$ErrorActionPreference = 'Stop'

if (-not $Path) {
    $scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $Path = Join-Path $scriptRoot '..\raw\obsidian\outputs'
}
$Path = (Resolve-Path -LiteralPath $Path).Path

# YYYYMM (6자리 숫자) 패턴과 충돌하지 않는 폴더는 보호하지 않아도 안전하지만,
# 혹시라도 수집 폴더를 이동 대상으로 잡지 않도록 알려진 다른 이름들을 방어적으로 유지한다.
$ProtectedDirs = @('attachments')

function Get-DocDate {
    param([System.IO.FileInfo]$File)
    if ($File.Extension -ieq '.md') {
        $head = Get-Content -LiteralPath $File.FullName -TotalCount 80 -ErrorAction SilentlyContinue
        $inFm = $false
        $fmLines = @()
        foreach ($line in $head) {
            if ($line -match '^---\s*$') {
                if (-not $inFm) { $inFm = $true; continue } else { break }
            }
            if ($inFm) { $fmLines += $line }
        }
        foreach ($key in @('created', 'updated')) {
            foreach ($l in $fmLines) {
                if ($l -match "^\s*$key\s*:\s*[`"']?(\d{4}-\d{2}-\d{2})") {
                    return [PSCustomObject]@{ Date = $Matches[1]; Source = "fm:$key" }
                }
            }
        }
    }
    return [PSCustomObject]@{ Date = $File.LastWriteTime.ToString('yyyy-MM-dd'); Source = 'mtime' }
}

if (-not (Test-Path -LiteralPath $Path)) {
    Write-Error "Outputs path not found: $Path"
    exit 1
}

$files = Get-ChildItem -LiteralPath $Path -File
if (-not $files) {
    Write-Host "No top-level files to organize." -ForegroundColor DarkGray
    exit 0
}

$plan = foreach ($f in $files) {
    $d = Get-DocDate $f
    $folder = ($d.Date -replace '-', '').Substring(0, 6)
    [PSCustomObject]@{
        File   = $f.Name
        Date   = $d.Date
        Folder = $folder
        Source = $d.Source
        From   = $f.FullName
        To     = Join-Path (Join-Path $Path $folder) $f.Name
    }
}

# Summary
$plan | Group-Object Folder | Sort-Object Name | ForEach-Object {
    Write-Host ("{0} : {1} files" -f $_.Name, $_.Count) -ForegroundColor Cyan
}
Write-Host "--- source breakdown ---"
$plan | Group-Object Source | Sort-Object Name | ForEach-Object {
    Write-Host ("  {0,-12} {1}" -f $_.Name, $_.Count)
}
Write-Host ("--- total: {0} files ---" -f $plan.Count)

# Sanity check: no protected dir collision
$bad = $plan | Where-Object { $ProtectedDirs -contains $_.Folder }
if ($bad) {
    Write-Error "Refusing to move into protected directory name. Aborting."
    exit 2
}

$moved = 0
$collisions = 0
foreach ($item in $plan) {
    $destDir = Split-Path $item.To -Parent
    if (-not (Test-Path -LiteralPath $destDir)) {
        if ($PSCmdlet.ShouldProcess($destDir, 'Create directory')) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
    }
    if (Test-Path -LiteralPath $item.To) {
        Write-Warning "COLLISION: $($item.To) already exists. Skipping."
        $collisions++
        continue
    }
    if ($PSCmdlet.ShouldProcess($item.From, "Move -> $($item.To)")) {
        Move-Item -LiteralPath $item.From -Destination $item.To
        $moved++
    }
}

Write-Host ""
Write-Host ("Moved: {0}   Collisions: {1}   Planned: {2}" -f $moved, $collisions, $plan.Count) -ForegroundColor Green
