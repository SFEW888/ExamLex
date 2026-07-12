param(
    [ValidateSet("codex", "claude", "cursor")]
    [string]$Agent = "codex",
    [switch]$Project,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$NoForce,
    [switch]$Help
)

$ErrorActionPreference = "Stop"
$RepositoryUrl = "https://github.com/SFEW888/ExamLex"

if ($Help) {
    Write-Host "Usage: .\install.ps1 [codex|claude|cursor] [-Project] [-DryRun] [-Force]"
    Write-Host "Repository: $RepositoryUrl"
    Write-Host "Clone: git clone $RepositoryUrl.git"
    exit 0
}

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python 3.10+ is required for the installer."
}
$versionText = & $python.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
if ($LASTEXITCODE -ne 0) {
    throw "Unable to determine Python version. Python 3.10+ is required for the installer."
}
try {
    $pythonVersion = [version]($versionText | Select-Object -Last 1)
} catch {
    throw "Unable to determine Python version. Python 3.10+ is required for the installer."
}
if ($pythonVersion -lt [version]"3.10") {
    throw "Python 3.10+ is required for the installer. Found Python $pythonVersion."
}

$script = Join-Path $PSScriptRoot "scripts\install_$Agent.py"
$argsList = @($script)

if ($Project) {
    if ($Agent -eq "codex") {
        $argsList += @("--dest", ".agents\skills")
    } elseif ($Agent -eq "claude") {
        $argsList += @("--dest", ".claude\skills")
    } else {
        $argsList += @("--dest", ".cursor\skills")
    }
}

if ($DryRun) {
    $argsList += @("--dry-run", "--json")
}

if ($Force -and -not $NoForce) {
    $argsList += "--force"
}

& $python.Source @argsList
exit $LASTEXITCODE
