# Apply Git user config from .env.git (keeps credentials out of scripts)
# Run once: .\setup-git-config.ps1

$envFile = Join-Path $PSScriptRoot ".env.git"
if (-not (Test-Path $envFile)) {
    Write-Host "Create .env.git with GIT_USER_NAME and GIT_USER_EMAIL" -ForegroundColor Red
    exit 1
}

$name = $null
$email = $null
Get-Content $envFile | ForEach-Object {
    if ($_ -match '^\s*GIT_USER_NAME=(.+)$') { $name = $matches[1].Trim() }
    if ($_ -match '^\s*GIT_USER_EMAIL=(.+)$') { $email = $matches[1].Trim() }
}

if (-not $name -or -not $email) {
    Write-Host "Missing GIT_USER_NAME or GIT_USER_EMAIL in .env.git" -ForegroundColor Red
    exit 1
}

& "C:\Program Files\Git\bin\git.exe" config --global user.name $name
& "C:\Program Files\Git\bin\git.exe" config --global user.email $email
Write-Host "Git config set: $name <$email>" -ForegroundColor Green
