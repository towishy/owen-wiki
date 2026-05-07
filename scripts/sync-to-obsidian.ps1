# Sync wiki/ changes to raw/obsidian/outputs/reports/ (incremental)
#
# user memory: "wiki/ 하위에 md 문서 생성/업데이트 시 raw/obsidian/outputs/reports/에도 동일 파일 복사본 생성"
#
# Usage:
#   pwsh scripts/sync-to-obsidian.ps1               # last 24h changed files
#   pwsh scripts/sync-to-obsidian.ps1 -All          # full sync
#   pwsh scripts/sync-to-obsidian.ps1 -Hours 72     # custom window
#   pwsh scripts/sync-to-obsidian.ps1 -DryRun       # report only

[CmdletBinding()]
param(
  [switch]$All,
  [int]$Hours = 24,
  [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$src = Join-Path $repoRoot 'wiki'
$dst = Join-Path $repoRoot 'raw\obsidian\outputs\reports'

if (-not (Test-Path $src)) { Write-Error "wiki/ not found: $src"; exit 1 }
if (-not (Test-Path $dst)) {
  if ($DryRun) {
    Write-Host "[DRY-RUN] Would create: $dst"
  } else {
    New-Item -ItemType Directory -Path $dst -Force | Out-Null
  }
}

$cutoff = (Get-Date).AddHours(-$Hours)
$files = Get-ChildItem $src -Recurse -File -Filter *.md | Where-Object {
  $_.Name -notin @('_index.md', 'README.md') -and
  $_.FullName -notmatch '\\ontology\\' -and
  ($All.IsPresent -or $_.LastWriteTime -ge $cutoff)
}

Write-Host "Files to sync: $($files.Count) (mode: $(if($All){'ALL'}else{"last $Hours h"}))"

$copied = 0
$skipped = 0
foreach ($f in $files) {
  $rel = $f.FullName.Substring($src.Length).TrimStart('\','/')
  $target = Join-Path $dst $rel
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
