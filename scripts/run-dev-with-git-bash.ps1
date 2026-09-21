param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $Arguments
)

$ErrorActionPreference = "Stop"

# Find Git for Windows from git.exe
$gitCommand = Get-Command git.exe -ErrorAction SilentlyContinue |
    Select-Object -First 1

if (-not $gitCommand -or -not $gitCommand.Source) {
    throw "Git for Windows was not found."
}

# git.exe is usually under: C:\Program Files\Git\cmd\git.exe
$gitRoot = Split-Path `
    (Split-Path -Parent $gitCommand.Source) `
    -Parent

$bashCandidates = @(
    (Join-Path $gitRoot "bin\bash.exe"),
    (Join-Path $gitRoot "usr\bin\bash.exe")
)

$bashExe = $bashCandidates |
    Where-Object { Test-Path -LiteralPath $_ } |
    Select-Object -First 1

if (-not $bashExe) {
    throw "Git for Windows Bash not found under: $gitRoot"
}

Write-Host "Using Git Bash: $bashExe"

# Ensure Windows-installed tools are visible inside Git Bash
$toolDirectories = @()

$uvDirectory = Join-Path $env:USERPROFILE ".local\bin"
if (Test-Path -LiteralPath $uvDirectory) {
    $toolDirectories += $uvDirectory
}

foreach ($toolName in @("uv.exe", "node.exe", "pnpm.cmd", "nginx.exe")) {
    $tool = Get-Command $toolName -ErrorAction SilentlyContinue |
        Select-Object -First 1

    if ($tool -and $tool.Source) {
        $toolDirectories += Split-Path -Parent $tool.Source
    }
}

$pathEntries = @(
    $toolDirectories
    (Join-Path $gitRoot "usr\bin")
    (Join-Path $gitRoot "mingw64\bin")
    $env:Path
) |
    Where-Object { $_ } |
    Select-Object -Unique

$env:Path = $pathEntries -join ";"

Write-Host "Detected Windows - using Git Bash..."

& $bashExe --noprofile --norc @Arguments
$bashExitCode = $LASTEXITCODE

if ($bashExitCode -in @(2, 130, 143, 255, 512)) {
    exit 0
}

exit $bashExitCode