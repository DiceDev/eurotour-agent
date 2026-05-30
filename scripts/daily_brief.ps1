param(
    [string]$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path,
    [string]$OutputDir = "runs\latest",
    [string]$Watchlist = "data\watchlist.example.yaml",
    [string]$Findings = "",
    [string]$MusicTaste = "",
    [string]$Rates = "",
    [string]$History = "data\trip_history.example.yaml",
    [string]$Prices = "data\price_history.example.yaml",
    [double]$DropThresholdPercent = 10.0
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $ProjectRoot

$arguments = @(
    "-m", "eurotour_agent.scheduler", "daily-brief-run",
    "--watchlist", $Watchlist,
    "--output-dir", $OutputDir,
    "--drop-threshold-percent", "$DropThresholdPercent"
)

if ($Findings) {
    $arguments += @("--findings", $Findings)
}
if ($MusicTaste) {
    $arguments += @("--music-taste", $MusicTaste)
}
if ($Rates) {
    $arguments += @("--rates", $Rates)
}
if ($History) {
    $arguments += @("--history", $History)
}
if ($Prices) {
    $arguments += @("--prices", $Prices)
}

python @arguments
