param(
    [ValidateSet("codex", "claude", "cursor")]
    [string]$Agent = "codex",
    [switch]$Project,
    [switch]$DryRun,
    [switch]$NoForce
)

$ErrorActionPreference = "Stop"

$python = Get-Command python -ErrorAction SilentlyContinue
if (-not $python) {
    $python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $python) {
    throw "Python 3.10+ is required for the installer."
}

$script = Join-Path $PSScriptRoot "scripts\install_$Agent.py"
$argsList = @($script)

if ($Project) {
    if ($Agent -eq "codex") {
        $argsList += @("--dest", ".agents\skills")
    } elseif ($Agent -eq "claude") {
        $argsList += @("--dest", ".claude\skills")
    } else {
        $argsList += @("--dest", ".cursor\rules\skills")
    }
}

if ($DryRun) {
    $argsList += @("--dry-run", "--json")
}

if (-not $NoForce) {
    $argsList += "--force"
}

& $python.Source @argsList
exit $LASTEXITCODE
