# Sync wiki/ changes to an external Obsidian vault folder (incremental).
#
# 위키 페이지 변경분만 외부 Obsidian 볼트(예: 백업/공유용)로 증분 복사.
# wiki/ 변경 시 자동 동기 hook으로 사용 가능.
#
# Usage:
#   pwsh scripts/sync-to-obsidian.ps1 -Destination "D:\Obsidian\WikiMirror"
#   pwsh scripts/sync-to-obsidian.ps1 -Destination "/Users/me/Obsidian/wiki" -All
#   pwsh scripts/sync-to-obsidian.ps1 -Destination $env:OBSIDIAN_MIRROR -Hours 72 -DryRun
#
# Destination을 매번 지정하기 싫으면 환경변수로 설정:
#   $env:OBSIDIAN_MIRROR = "D:\Obsidian\WikiMirror"   # 또는 셸 프로파일에 영구 등록
#
# 양 OS 호환: PowerShell Core 7+ (pwsh)

[CmdletBinding()]
param(
  [string]$Destination = $env:OBSIDIAN_MIRROR,
  [switch]$All,
  [int]$Hours = 24,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repoRoot 'wiki'

if ([string]::IsNullOrWhiteSpace($Destination)) {
  Write-Error "Destination not set. Pass -Destination <path> or set `$env:OBSIDIAN_MIRROR."
  exit 1
}

if (-not (Test-Path $src)) { Write-Error "wiki/ not found: $src"; exit 1 }
if (-not (Test-Path $Destination)) {
  if ($DryRun) {
    Write-Host "[DRY-RUN] Would create: $Destination"
  } else {
    New-Item -ItemType Directory -Path $Destination -Force | Out-Null
  }
}

$cutoff = (Get-Date).AddHours(-$Hours)
$files = Get-ChildItem $src -Recurse -File -Filter *.md | Where-Object {
  $_.Name -notin @('_index.md', 'README.md') -and
  $_.FullName -notmatch '[\\/]ontology[\\/]' -and
  ($All.IsPresent -or $_.LastWriteTime -ge $cutoff)
}

Write-Host "Source: $src"
Write-Host "Destination: $Destination"
Write-Host "Files to sync: $($files.Count) (mode: $(if($All){'ALL'}else{"last $Hours h"}))"

$copied = 0
$skipped = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($src.Length).TrimStart('\','/')
  $target = Join-Path $Destination $rel
  $targetDir = Split-Path $target -Parent
  if ($DryRun) {
    Write-Host "  [DRY] $rel"
    continue
  }
  if (-not (Test-Path $targetDir)) {
    New-Item -ItemType Directory -Path $targetDir -Force | Out-Null
  }
  if ((Test-Path $target) -and ((Get-Item $target).LastWriteTime -ge $f.LastWriteTime)) {
    $skipped++
    continue
  }
  Copy-Item $f.FullName -Destination $target -Force
  $copied++
}
Write-Host "Copied: $copied, Skipped (up-to-date): $skipped"
