[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$TaskName = "ExamLex Capacity Monitor",
    [string]$PythonExecutable = "",
    [string]$SessionsRoot = "",
    [string]$StrategyLibrary = "",
    [ValidateRange(5, 1440)]
    [int]$IntervalMinutes = 30,
    [switch]$Uninstall
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $PSScriptRoot

if ($Uninstall) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        if ($PSCmdlet.ShouldProcess($TaskName, "Unregister scheduled task")) {
            Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        }
    }
    return
}

if (-not $PythonExecutable) {
    $PythonExecutable = (Get-Command python -ErrorAction Stop).Source
}
if (-not $SessionsRoot) {
    $SessionsRoot = Join-Path $env:LOCALAPPDATA "ExamLex\sessions"
}
if (-not $StrategyLibrary) {
    $StrategyLibrary = Join-Path $env:LOCALAPPDATA "ExamLex\strategy-library.db"
}

function Quote-Argument([string]$Value) {
    return '"' + $Value.Replace('"', '\"') + '"'
}

$arguments = @(
    "-m",
    "examlex",
    "capacity-monitor",
    "--sessions-root",
    (Quote-Argument $SessionsRoot),
    "--strategy-library",
    (Quote-Argument $StrategyLibrary),
    "--notify-windows"
) -join " "

$action = New-ScheduledTaskAction `
    -Execute $PythonExecutable `
    -Argument $arguments `
    -WorkingDirectory $repoRoot
$trigger = New-ScheduledTaskTrigger `
    -Once `
    -At (Get-Date).AddMinutes(1) `
    -RepetitionInterval (New-TimeSpan -Minutes $IntervalMinutes)
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 15)
$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

if ($PSCmdlet.ShouldProcess($TaskName, "Register per-user background capacity monitor")) {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Prunes regenerable ExamLex artifacts and warns before strategy data grows too large." `
        -Force | Out-Null
}

[pscustomobject]@{
    TaskName = $TaskName
    IntervalMinutes = $IntervalMinutes
    PythonExecutable = $PythonExecutable
    SessionsRoot = $SessionsRoot
    StrategyLibrary = $StrategyLibrary
    AutomaticStrategyDeletion = $false
}
