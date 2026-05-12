<#
.SYNOPSIS
    수집 폴더(raw/articles/, raw/obsidian/Clippings/) 직속 신규 파일을 생성월(YYYYMM) 폴더로 정리한다.

.DESCRIPTION
    - 두 수집 폴더에만 적용한다 (정책: AGENTS.md 의 "수집 폴더 월별 정책").
    - 기존 큐레이션/하위 폴더는 절대 건드리지 않는다 (예: articles/azdo-scim-wiki/, articles/mslearn/,
      Clippings/attachments/ 등). 이름이 6자리 숫자(YYYYMM)인 폴더만 월별 폴더로 인정하고, 나머지
      이름의 하위 폴더는 모두 보호 대상이다.
    - 직속 파일만 대상으로 한다. 마크다운이면 frontmatter `created` -> `updated` -> 파일 mtime 순으로
      날짜를 결정하고, 그 외 형식은 mtime을 사용한다.
    - 대상 폴더 (예: articles/202606/)가 없으면 자동 생성한다.

.PARAMETER ArticlesPath
    raw/articles 경로. 생략 시 스크립트 위치 기준 ../raw/articles 사용.

.PARAMETER ClippingsPath
    raw/obsidian/Clippings 경로. 생략 시 스크립트 위치 기준 ../raw/obsidian/Clippings 사용.

.PARAMETER Only
    특정 한쪽만 처리. articles | clippings (생략 시 양쪽 모두).

.PARAMETER WhatIf
    실제 이동 없이 계획만 출력.

.EXAMPLE
    pwsh ./scripts/organize-collection-by-month.ps1 -WhatIf
    pwsh ./scripts/organize-collection-by-month.ps1
    pwsh ./scripts/organize-collection-by-month.ps1 -Only clippings
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$ArticlesPath,
    [string]$ClippingsPath,
    [ValidateSet('articles', 'clippings')]
    [string]$Only
)

$ErrorActionPreference = 'Stop'

$scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
if (-not $ArticlesPath)  { $ArticlesPath  = Join-Path $scriptRoot '..\raw\articles' }
if (-not $ClippingsPath) { $ClippingsPath = Join-Path $scriptRoot '..\raw\obsidian\Clippings' }

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

function Invoke-FolderOrganize {
    param(
        [Parameter(Mandatory)] [string]$Label,
        [Parameter(Mandatory)] [string]$RootPath
    )
    if (-not (Test-Path -LiteralPath $RootPath)) {
        Write-Warning "[$Label] path not found: $RootPath  (skipped)"
        return
    }
    $RootPath = (Resolve-Path -LiteralPath $RootPath).Path
    Write-Host ""
    Write-Host "=== $Label : $RootPath ===" -ForegroundColor Cyan

    $files = Get-ChildItem -LiteralPath $RootPath -File
    if (-not $files) {
        Write-Host "  No top-level files to organize." -ForegroundColor DarkGray
        return
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
            To     = Join-Path (Join-Path $RootPath $folder) $f.Name
        }
    }

    # 보호 검사: YYYYMM 패턴이 아닌 기존 하위 폴더 이름과 충돌하면 거부
    $existingSubdirs = Get-ChildItem -LiteralPath $RootPath -Directory | Select-Object -ExpandProperty Name
    $protectedNames = $existingSubdirs | Where-Object { $_ -notmatch '^\d{6}$' }
    $bad = $plan | Where-Object { $protectedNames -contains $_.Folder }
    if ($bad) {
        Write-Error "[$Label] Refusing to move into a protected (non-YYYYMM) subfolder. Aborting this folder."
        return
    }

    $plan | Group-Object Folder | Sort-Object Name | ForEach-Object {
        Write-Host ("  {0} : {1} files" -f $_.Name, $_.Count) -ForegroundColor Cyan
    }
    Write-Host "  --- source breakdown ---"
    $plan | Group-Object Source | Sort-Object Name | ForEach-Object {
        Write-Host ("    {0,-12} {1}" -f $_.Name, $_.Count)
    }
    Write-Host ("  --- total: {0} files ---" -f $plan.Count)

    $moved = 0; $collisions = 0
    foreach ($item in $plan) {
        $destDir = Split-Path $item.To -Parent
        if (-not (Test-Path -LiteralPath $destDir)) {
            if ($PSCmdlet.ShouldProcess($destDir, 'Create directory')) {
                New-Item -ItemType Directory -Path $destDir -Force | Out-Null
            }
        }
        if (Test-Path -LiteralPath $item.To) {
            Write-Warning "  COLLISION: $($item.To) already exists. Skipping."
            $collisions++
            continue
        }
        if ($PSCmdlet.ShouldProcess($item.From, "Move -> $($item.To)")) {
            Move-Item -LiteralPath $item.From -Destination $item.To
            $moved++
        }
    }

    Write-Host ("  Moved: {0}   Collisions: {1}   Planned: {2}" -f $moved, $collisions, $plan.Count) -ForegroundColor Green
}

if (-not $Only -or $Only -eq 'articles')  { Invoke-FolderOrganize -Label 'articles'  -RootPath $ArticlesPath }
if (-not $Only -or $Only -eq 'clippings') { Invoke-FolderOrganize -Label 'clippings' -RootPath $ClippingsPath }
