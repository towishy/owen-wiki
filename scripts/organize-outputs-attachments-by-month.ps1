<#
.SYNOPSIS
    outputs/YYYYMM/attachments/ 와 outputs/attachments/(legacy)에 있는 첨부 파일을 참조 문서의 월 폴더로 재배치한다.

.DESCRIPTION
    - outputs/{YYYYMM}/*.md 문서의 이미지 참조를 스캔해 첨부 → 월 매핑을 만든다.
    - 매핑 규칙:
        * 단일 월에서만 참조 → 그 월의 attachments/ 로 이동
        * 여러 월에서 참조  → 가장 많이 참조된 월 (동률 시 가장 빠른 월) 로 이동, 다른 월 문서의 상대경로를
                              `../YYYYMM/Attachments/...` 로 자동 업데이트
        * 어떤 문서도 참조 안 함 → 파일 mtime 기준 YYYYMM 폴더로 이동
    - markdown 스타일 `![alt](Attachments/foo.svg)` 와 wikilink `![[foo.svg]]` 둘 다 인식.
    - 이미 올바른 월 폴더에 있는 첨부는 건드리지 않음.

.PARAMETER OutputsPath
    outputs 루트 경로. 생략 시 스크립트 위치 기준 ../raw/obsidian/outputs (양 OS 호환).

.PARAMETER WhatIf
    실제 이동/수정 없이 계획만 출력.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$OutputsPath
)

$ErrorActionPreference = 'Stop'

if (-not $OutputsPath) {
    $scriptRoot = if ($PSScriptRoot) { $PSScriptRoot } else { Split-Path -Parent $MyInvocation.MyCommand.Path }
    $OutputsPath = Join-Path $scriptRoot '..\raw\obsidian\outputs'
}
$OutputsPath = (Resolve-Path -LiteralPath $OutputsPath).Path

# 1) 모든 월 폴더 수집 + 신규 파일이 없으면 조기 종료
$monthDirs = Get-ChildItem -LiteralPath $OutputsPath -Directory | Where-Object { $_.Name -match '^\d{6}$' }
if (-not $monthDirs) { Write-Host "No month folders found." -ForegroundColor DarkGray; exit 0 }

# 2) 이동 후보 첨부 수집: outputs/attachments/(legacy 루트) + outputs/{YYYYMM}/attachments/
$candidateRoots = @()
$legacyRoot = Join-Path $OutputsPath 'attachments'
if (Test-Path -LiteralPath $legacyRoot) { $candidateRoots += @{ Path = $legacyRoot; CurrentMonth = $null } }
foreach ($md in $monthDirs) {
    $mAtt = Join-Path $md.FullName 'attachments'
    if (Test-Path -LiteralPath $mAtt) { $candidateRoots += @{ Path = $mAtt; CurrentMonth = $md.Name } }
}
if (-not $candidateRoots) { Write-Host "No attachments folders found." -ForegroundColor DarkGray; exit 0 }

$attMap = @{}    # name(lc) -> @{ FileInfo, CurrentMonth }
foreach ($root in $candidateRoots) {
    foreach ($f in (Get-ChildItem -LiteralPath $root.Path -File -ErrorAction SilentlyContinue)) {
        $key = $f.Name.ToLower()
        if (-not $attMap.ContainsKey($key)) {
            $attMap[$key] = [PSCustomObject]@{ File = $f; CurrentMonth = $root.CurrentMonth }
        }
    }
}
if ($attMap.Count -eq 0) { Write-Host "No attachment files found." -ForegroundColor DarkGray; exit 0 }

# 3) 모든 월 폴더 문서 스캔하여 참조 수집: basename(소문자) → @{ month → @(referring file paths) }
$refMap = @{}
$mdRefRe   = '!\[[^\]]*\]\(([^)]+)\)'
$wikiRefRe = '!\[\[([^\]|#]+)(?:[#|][^\]]*)?\]\]'

function Add-Ref {
    param([string]$Name, [string]$Month, [string]$Doc)
    $key = $Name.ToLower()
    if (-not $refMap.ContainsKey($key)) { $refMap[$key] = @{} }
    if (-not $refMap[$key].ContainsKey($Month)) { $refMap[$key][$Month] = @() }
    $refMap[$key][$Month] += $Doc
}

foreach ($md in ($monthDirs | ForEach-Object { Get-ChildItem -LiteralPath $_.FullName -Filter *.md -File })) {
    $month = (Split-Path (Split-Path $md.FullName -Parent) -Leaf)
    $text = Get-Content -LiteralPath $md.FullName -Raw -ErrorAction SilentlyContinue
    if (-not $text) { continue }
    foreach ($m in [regex]::Matches($text, $mdRefRe)) {
        $url = $m.Groups[1].Value.Trim()
        $url = ($url -split '\s')[0]
        if ($url -notmatch '^[A-Za-z][A-Za-z0-9+.-]*://') {
            $name = Split-Path $url -Leaf
            if ($name -and $attMap.ContainsKey($name.ToLower())) {
                Add-Ref -Name $name -Month $month -Doc $md.FullName
            }
        }
    }
    foreach ($m in [regex]::Matches($text, $wikiRefRe)) {
        $name = Split-Path $m.Groups[1].Value.Trim() -Leaf
        if ($name -and $attMap.ContainsKey($name.ToLower())) {
            Add-Ref -Name $name -Month $month -Doc $md.FullName
        }
    }
}

# 4) 첨부별 타깃 월 결정
$plan = foreach ($entry in $attMap.GetEnumerator()) {
    $f = $entry.Value.File
    $current = $entry.Value.CurrentMonth
    $key = $entry.Key
    $months = $null
    if ($refMap.ContainsKey($key)) { $months = $refMap[$key] }
    if ($months -and $months.Count -ge 1) {
        $best = $months.GetEnumerator() | Sort-Object @{Expression={$_.Value.Count}; Descending=$true}, Name | Select-Object -First 1
        $target = $best.Key
        $source = if ($months.Count -eq 1) { 'ref:single' } else { "ref:multi($($months.Count))" }
        $crossDocs = @()
        if ($months.Count -gt 1) {
            foreach ($kv in $months.GetEnumerator()) {
                if ($kv.Key -ne $target) {
                    $crossDocs += $kv.Value | ForEach-Object { [PSCustomObject]@{ Doc=$_; FromMonth=$kv.Key } }
                }
            }
        }
        [PSCustomObject]@{
            File         = $f.Name
            CurrentMonth = $current
            Target       = $target
            Source       = $source
            CrossDocs    = $crossDocs
            FullPath     = $f.FullName
        }
    } else {
        $target = $f.LastWriteTime.ToString('yyyyMM')
        [PSCustomObject]@{
            File         = $f.Name
            CurrentMonth = $current
            Target       = $target
            Source       = 'mtime'
            CrossDocs    = @()
            FullPath     = $f.FullName
        }
    }
}

# 이미 올바른 월에 있는 첨부는 제외
$plan = @($plan | Where-Object { $_.CurrentMonth -ne $_.Target })
if ($plan.Count -eq 0) { Write-Host "All attachments already in correct month folders." -ForegroundColor DarkGray; exit 0 }

# 5) Summary
$plan | Group-Object Target | Sort-Object Name | ForEach-Object {
    Write-Host ("  -> {0}/attachments/  : {1}" -f $_.Name, $_.Count) -ForegroundColor Cyan
}
Write-Host "--- source breakdown ---"
$plan | Group-Object Source | Sort-Object Name | ForEach-Object {
    Write-Host ("  {0,-14} {1}" -f $_.Name, $_.Count)
}
$crossTotal = ($plan | Where-Object { $_.CrossDocs.Count -gt 0 } | ForEach-Object { $_.CrossDocs.Count } | Measure-Object -Sum).Sum
Write-Host ("--- cross-month docs to rewrite: {0} doc-references ---" -f ([int]$crossTotal))

# Show cross-month details if any
foreach ($p in $plan | Where-Object { $_.CrossDocs.Count -gt 0 }) {
    Write-Host ("  {0} -> {1}; rewrite in:" -f $p.File, $p.Target) -ForegroundColor Yellow
    foreach ($c in $p.CrossDocs) {
        Write-Host ("     {0}  ({1})" -f (Split-Path $c.Doc -Leaf), $c.FromMonth)
    }
}

# 6) Execute moves
$moved = 0; $rewritten = 0
foreach ($p in $plan) {
    $destDir = Join-Path (Join-Path $OutputsPath $p.Target) 'attachments'
    if (-not (Test-Path -LiteralPath $destDir)) {
        if ($PSCmdlet.ShouldProcess($destDir, 'Create directory')) {
            New-Item -ItemType Directory -Path $destDir -Force | Out-Null
        }
    }
    $src = $p.FullPath
    $dst = Join-Path $destDir $p.File
    if ($src -ieq $dst) { continue }
    if (Test-Path -LiteralPath $dst) {
        Write-Warning "COLLISION: $dst exists. Skipping."
        continue
    }
    if ($PSCmdlet.ShouldProcess($src, "Move -> $dst")) {
        Move-Item -LiteralPath $src -Destination $dst
        $moved++
    }

    # 6) Rewrite cross-month doc references
    foreach ($c in $p.CrossDocs) {
        $doc = $c.Doc
        $text = Get-Content -LiteralPath $doc -Raw
        $orig = $text
        # Patterns to rewrite: (Attachments/file ...) and (attachments/file ...) at end of url
        $escaped = [regex]::Escape($p.File)
        # Replace markdown style: keep alt text intact, only replace the URL portion that ends in /file.ext
        $pattern = "(?<lead>!\[[^\]]*\]\()(?<pre>[^)]*?)(?<path>(?:\.\./)*[Aa]ttachments/$escaped)(?<post>[^)]*\))"
        $text = [regex]::Replace($text, $pattern, {
            param($m)
            $newPath = "../$($p.Target)/Attachments/$($p.File)"
            return $m.Groups['lead'].Value + $m.Groups['pre'].Value + $newPath + ($m.Groups['post'].Value)
        })
        if ($text -ne $orig) {
            if ($PSCmdlet.ShouldProcess($doc, "Rewrite path -> ../$($p.Target)/Attachments/$($p.File)")) {
                Set-Content -LiteralPath $doc -Value $text -NoNewline:$false -Encoding UTF8
                $rewritten++
            }
        }
    }
}

Write-Host ""
Write-Host ("Moved: {0}   Rewritten doc refs: {1}" -f $moved, $rewritten) -ForegroundColor Green
