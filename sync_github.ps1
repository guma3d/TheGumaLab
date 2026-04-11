param (
    [string]$TaskMessage = ""
)

# Detect current PC by hostname and map to commit prefix
$HostName = [System.Net.Dns]::GetHostName()
switch -Wildcard ($HostName) {
    "Guma3D"    { $Prefix = "HomeServerMain" }
    "guma3d-n"  { $Prefix = "Gram" }
    default     { $Prefix = "SurfacePro" }
}

if ([string]::IsNullOrWhiteSpace($TaskMessage)) {
    $TaskMessage = Read-Host "Enter short commit message summary (in English)"
}

$CommitMessage = "($Prefix) $TaskMessage"

# Ensure Git is on PATH for this session
$env:PATH += ";C:\Program Files\Git\cmd"

Write-Host "========== Git Sync Started — host=$HostName, prefix=($Prefix) ==========" -ForegroundColor Cyan

Write-Host "1. Adding files..."
git add .

$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit." -ForegroundColor Yellow
} else {
    Write-Host "2. Committing changes..."
    git commit -m $CommitMessage
}

Write-Host "3. Pulling latest from remote (rebase)..."
git pull origin main --rebase

Write-Host "4. Pushing to GitHub..."
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "========== Sync Completed Successfully! ==========" -ForegroundColor Green
} else {
    Write-Host "========== Sync Failed! Check the error messages above ==========" -ForegroundColor Red
}

pause
