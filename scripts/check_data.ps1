# ============================================================
# check_data.ps1 — English Exam AI Tutor 数据诊断
# 用法: .\scripts\check_data.ps1 [--data-dir <path>]
# 检查学习者档案、台账、策略库的完整性和大小
# ============================================================

param(
    [string]$DataDir = ".\local\data"
)

$ErrorActionPreference = "Continue"
$totalSizeMB = 0

function Write-Section($title) {
    Write-Host ""
    Write-Host "========== $title =========="
}

function Format-Size($bytes) {
    if ($bytes -gt 1MB) { return "$([math]::Round($bytes/1MB,1)) MB" }
    if ($bytes -gt 1KB) { return "$([math]::Round($bytes/1KB,1)) KB" }
    return "$bytes B"
}

function Write-Item($label, $path, $detail) {
    if (Test-Path $path) {
        $items = Get-ChildItem $path -Recurse -ErrorAction SilentlyContinue
        $size = ($items | Measure-Object -Property Length -Sum).Sum
        $script:totalSizeMB += [math]::Round($size/1MB, 1)
        Write-Host "  $label : $(Format-Size $size)" -ForegroundColor Green
        if ($detail) { Write-Host "    $detail" -ForegroundColor DarkGray }
    } else {
        Write-Host "  $label : Not Found" -ForegroundColor DarkGray
    }
}

Write-Section "Data Directory: $DataDir"
if (-not (Test-Path $DataDir)) {
    Write-Host "  Data directory not found. Create it or run with --data-dir <path>." -ForegroundColor Yellow
    exit 0
}

Write-Section "Learner Data"

Write-Item "Learner Profiles" "$DataDir\learner-profiles" ""
$profileCount = if (Test-Path "$DataDir\learner-profiles") {
    (Get-ChildItem "$DataDir\learner-profiles" -File -ErrorAction SilentlyContinue).Count
} else { 0 }
Write-Host "    Files: $profileCount"

Write-Item "Ability Profiles" "$DataDir\ability-profiles" ""
$abilityCount = if (Test-Path "$DataDir\ability-profiles") {
    (Get-ChildItem "$DataDir\ability-profiles" -File -ErrorAction SilentlyContinue).Count
} else { 0 }
Write-Host "    Files: $abilityCount"

Write-Item "Practice Ledgers" "$DataDir\practice-ledgers" ""
$ledgerCount = if (Test-Path "$DataDir\practice-ledgers") {
    (Get-ChildItem "$DataDir\practice-ledgers" -File -ErrorAction SilentlyContinue).Count
} else { 0 }
Write-Host "    Files: $ledgerCount"

Write-Item "Error Summaries" "$DataDir\error-summaries" ""
Write-Item "Writing Versions" "$DataDir\writing-versions" ""

Write-Section "Strategy Library"
$strategyPath = "$DataDir\strategy-library.json"
if (Test-Path $strategyPath) {
    try {
        $lib = Get-Content $strategyPath -Raw | ConvertFrom-Json
        $stratCount = $lib.strategies.Count
        Write-Host "  Strategies: $stratCount" -ForegroundColor Green

        $byExam = @{}
        foreach ($s in $lib.strategies) {
            foreach ($e in $s.exam_types) {
                $byExam[$e] = ($byExam[$e] ?? 0) + 1
            }
        }
        foreach ($exam in $byExam.Keys | Sort-Object) {
            Write-Host "    $exam : $($byExam[$exam])"
        }
    } catch {
        Write-Host "  strategy-library.json : PARSE ERROR — $($_.Exception.Message)" -ForegroundColor Red
    }
} else {
    Write-Host "  strategy-library.json : Not Found (no strategies ingested yet)" -ForegroundColor DarkGray
}

Write-Section "Ability History"
$historyPath = "$DataDir\ability-history.json"
if (Test-Path $historyPath) {
    try {
        $hist = Get-Content $historyPath -Raw | ConvertFrom-Json
        Write-Host "  Entries: $($hist.Count)" -ForegroundColor Green
    } catch {
        Write-Host "  ability-history.json : PARSE ERROR" -ForegroundColor Red
    }
} else {
    Write-Host "  ability-history.json : Not Found" -ForegroundColor DarkGray
}

Write-Section "JSON Validity Check"
$failedFiles = @()
Get-ChildItem $DataDir -Recurse -Filter "*.json" -ErrorAction SilentlyContinue | ForEach-Object {
    try {
        Get-Content $_.FullName -Raw | ConvertFrom-Json | Out-Null
    } catch {
        $failedFiles += $_.FullName
    }
}

if ($failedFiles.Count -eq 0) {
    Write-Host "  All JSON files: VALID" -ForegroundColor Green
} else {
    Write-Host "  INVALID JSON files:" -ForegroundColor Red
    $failedFiles | ForEach-Object { Write-Host "    $_" -ForegroundColor Red }
}

Write-Section "Summary"
Write-Host "  Total data size: $totalSizeMB MB" -ForegroundColor Cyan
Write-Host "  Learner profiles: $profileCount"
Write-Host "  Practice ledgers: $ledgerCount"
