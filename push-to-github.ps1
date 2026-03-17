# Push Swift project to GitHub
# Run this after installing Git: https://git-scm.com/download/win

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "Initializing git..." -ForegroundColor Cyan
git init

Write-Host "Adding files..." -ForegroundColor Cyan
git add .

Write-Host "Committing..." -ForegroundColor Cyan
git commit -m "Initial commit: Swift Event Intelligence Platform"

Write-Host "Adding remote..." -ForegroundColor Cyan
git remote add origin https://github.com/ibrahimmarvinochieng-beep/swift.git

Write-Host "Pushing to main..." -ForegroundColor Cyan
git branch -M main
git push -u origin main

Write-Host "Done! View at https://github.com/ibrahimmarvinochieng-beep/swift" -ForegroundColor Green
