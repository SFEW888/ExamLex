# ============================================================
# maintenance.ps1 — English Exam AI Tutor 数据维护
# 用法: .\scripts\maintenance.ps1 [--data-dir <path>] [--dry-run]
# 清理旧备份、验证数据完整性、报告磁盘占用
# ============================================================

param(
    [string]$DataDir = ".\local\data",
    [switch]$DryRun,
    [switch]$Force
)

$ErrorActionPreference = "Continue"
$totalCleanedMB = 0
$script:DryRun = $DryRun

function Write-Action($label, $detail) {
    $prefix = if ($DryRun) { "[DRY-RUN] " } else { "" }
    Write-Host "$prefix$label" -ForegroundColor Cyan
    if ($detail) { Write-Host "  $detail" -ForegroundColor DarkGray }
}

function Remove-IfSafe($path, $description) {
    if (-not (Test-Path $path)) {
        Write-Host "  $description : Not Found (skip)" -ForegroundColor DarkGray
        return 0
    }
    $items = Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue
    $sizeMB = [math]::Round(($items | Measure-Object -Property Length -Sum).Sum / 1MB, 1)

    if ($DryRun) {
        Write-Host "  Would delete: $description ($sizeMB MB)" -ForegroundColor Yellow
        return 0
    }

    try {
        Remove-Item $path -Recurse -Force -ErrorAction Stop
        Write-Host "  Deleted: $description ($sizeMB MB)" -ForegroundColor Green
        return $sizeMB
    } catch {
        Write-Host "  Failed: $description — $($_.Exception.Message)" -ForegroundColor Red
        return 0
    }
}

Write-Host "========== English Exam AI Tutor — Maintenance =========="
if ($DryRun) {
    Write-Host "DRY-RUN mode: no files will be deleted." -ForegroundColor Yellow
}

# 1. Clean old backups (> 90 days)
Write-Host ""
Write-Host "--- Old Backups ---"
$backupPattern = "backup-*.tar.gz"
$oldDate = (Get-Date).AddDays(-90)
$oldBackups = Get-ChildItem $DataDir -Filter $backupPattern -ErrorAction SilentlyContinue |
    Where-Object { $_.LastWriteTime -lt $oldDate }

if ($oldBackups) {
    foreach ($b in $oldBackups) {
        $age = [math]::Round(((Get-Date) - $b.LastWriteTime).TotalDays, 0)
        $mb = [math]::Round($b.Length/1MB, 1)
        if ($DryRun) {
            Write-Host "  Would delete: $($b.Name) ($mb MB, ${age}d old)" -ForegroundColor Yellow
        } else {
            Remove-Item $b.FullName -Force
            Write-Host "  Deleted: $($b.Name) ($mb MB, ${age}d old)" -ForegroundColor Green
            $totalCleanedMB += $mb
        }
    }
} else {
    Write-Host "  No old backups found." -ForegroundColor DarkGray
}

# 2. Clean temp/working files
Write-Host ""
Write-Host "--- Temp Files ---"
$tempPaths = @(
    "$DataDir\tmp",
    "$DataDir\temp",
    "$DataDir\.working"
)
foreach ($tp in $tempPaths) {
    $cleaned = Remove-IfSafe $tp "Temp dir: $tp"
    $totalCleanedMB += $cleaned
}

# 3. Validate data integrity
Write-Host ""
Write-Host "--- Data Integrity ---"
$corruptFiles = @()
Get-ChildItem $DataDir -Recurse -Filter "*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        $content = Get-Content $_.FullName -Raw -ErrorAction Stop
        $null = $content | ConvertFrom-Json
    } catch {
        $corruptFiles += $_.FullName
    }
}

if ($corruptFiles.Count -eq 0) {
    Write-Host "  All JSON files: VALID" -ForegroundColor Green
} else {
    Write-Host "  CORRUPT JSON files (cannot auto-repair):" -ForegroundColor Red
    $corruptFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
}

# 4. Backup size report
Write-Host ""
Write-Host "--- Backup Summary ---"
$allBackups = Get-ChildItem $DataDir -Filter $backupPattern -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending

if ($allBackups) {
    $totalBackupMB = [math]::Round(($allBackups | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    Write-Host "  Backups: $($allBackups.Count) files, $totalBackupMB MB total"
    Write-Host "  Latest: $($allBackups[0].Name) ($([math]::Round($allBackups[0].Length/1MB,1)) MB)"
    if ($allBackups.Count -gt 5) {
        Write-Host "  TIP: $($allBackups.Count - 5) backups older than the 5 most recent. Consider cleaning." -ForegroundColor Yellow
    }
} else {
    Write-Host "  No backups found. Run: tutor backup $DataDir" -ForegroundColor DarkGray
}

Write-Host ""
Write-Host "========== Done =========="
if ($DryRun) {
    Write-Host "DRY-RUN complete. Run without --dry-run to apply changes." -ForegroundColor Yellow
} else {
    Write-Host "Cleaned: $totalCleanedMB MB" -ForegroundColor Green
}
Write-Host "Run .\scripts\check_data.ps1 to verify data after maintenance." -ForegroundColor DarkGray
