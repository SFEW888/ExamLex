# ============================================================
# check_env.ps1 — ExamLex 环境诊断
# 用法: .\scripts\check_env.ps1
# 检查 Python、Git、Skills 安装、磁盘空间
# ============================================================

$ErrorActionPreference = "Continue"
$allOk = $true

function Write-Check($label, $ok, $detail) {
    $mark = if ($ok) { "  PASS" } else { "  FAIL" }
    $color = if ($ok) { "Green" } else { "Red" }
    Write-Host "$mark  $label" -ForegroundColor $color
    if ($detail) { Write-Host "       $detail" -ForegroundColor DarkGray }
    if (-not $ok) { $script:allOk = $false }
}

Write-Host "========== Python =========="
try {
    $pyVer = python --version 2>&1
    Write-Check "python" $true $pyVer
} catch {
    Write-Check "python" $false "Python not found in PATH. Install Python 3.10+."
}

try {
    $pyPath = (Get-Command python).Source
    Write-Host "       Path: $pyPath"
} catch { }

Write-Host ""
Write-Host "========== Git =========="
try {
    $gitVer = git --version 2>&1
    Write-Check "git" $true $gitVer
} catch {
    Write-Check "git" $false "Git not found. Install from https://git-scm.com."
}

Write-Host ""
Write-Host "========== Skills Directories =========="
$skillDirs = @(
    @{Name="Claude Code"; Path="$env:USERPROFILE\.claude\skills"},
    @{Name="Codex CLI";   Path="$env:USERPROFILE\.agents\skills"},
    @{Name="Cursor";      Path="$env:USERPROFILE\.cursor\skills"}
)

foreach ($dir in $skillDirs) {
    $exists = Test-Path $dir.Path
    if ($exists) {
        $count = (Get-ChildItem $dir.Path -Directory -ErrorAction SilentlyContinue).Count
        Write-Check $dir.Name $true "$($dir.Path) ($count skills)"
    } else {
        Write-Check $dir.Name $false "$($dir.Path) not found"
    }
}

Write-Host ""
Write-Host "========== Project Installation =========="
$projectPaths = @(
    @{Name="examlex (Claude)"; Path="$env:USERPROFILE\.claude\skills\examlex\SKILL.md"},
    @{Name="examlex (Codex)";  Path="$env:USERPROFILE\.agents\skills\examlex\SKILL.md"}
)

foreach ($p in $projectPaths) {
    $exists = Test-Path $p.Path
    Write-Check $p.Name $exists $(if ($exists) { $p.Path } else { "Not installed" })
}

Write-Host ""
Write-Host "========== Shortcut Skills =========="
$shortcuts = @(
    "learning-planner", "vocabulary-builder", "reading-navigator",
    "structure-planner", "grammar-corrector", "polish-wizard",
    "scenario-dialog", "culture-guide"
)

foreach ($sc in $shortcuts) {
    $found = $false
    foreach ($base in @("$env:USERPROFILE\.claude\skills", "$env:USERPROFILE\.agents\skills")) {
        if (Test-Path "$base\$sc\SKILL.md") { $found = $true; break }
    }
    Write-Check $sc $found ""
}

Write-Host ""
Write-Host "========== Disk Space =========="
$drives = @("C:", "D:")
foreach ($drive in $drives) {
    try {
        $disk = Get-PSDrive -Name $drive.Replace(":", "") -ErrorAction Stop
        $freeGB = [math]::Round($disk.Free/1GB, 1)
        $totalGB = [math]::Round(($disk.Used + $disk.Free)/1GB, 1)
        $pctFree = [math]::Round($disk.Free / ($disk.Used + $disk.Free) * 100, 0)
        $ok = $freeGB -gt 5
        Write-Check "$drive Free" $ok "$freeGB GB / $totalGB GB ($pctFree%)"
    } catch {
        Write-Check $drive $false "Drive not accessible"
    }
}

Write-Host ""
Write-Host "========== Result =========="
if ($allOk) {
    Write-Host "All checks passed." -ForegroundColor Green
} else {
    Write-Host "Some checks failed. Fix the FAIL items above." -ForegroundColor Yellow
}
