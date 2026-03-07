param (
    [string]$TaskMessage = ""
)

if ([string]::IsNullOrWhiteSpace($TaskMessage)) {
    $TaskMessage = Read-Host "간단한 커밋 작업 내용을 입력하세요"
}

$CommitMessage = "(SurfacePro) $TaskMessage"

# Git 경로 환경변수 추가 (세션 내 적용)
$env:PATH += ";C:\Program Files\Git\cmd"

Write-Host "========== Git Sync Started ==========" -ForegroundColor Cyan

# 변경 사항 확인 및 추가
Write-Host "1. Adding files..."
git add .

# 변경 사항이 없을 경우 커밋 생략을 위한 확인
$status = git status --porcelain
if ([string]::IsNullOrWhiteSpace($status)) {
    Write-Host "No changes to commit." -ForegroundColor Yellow
} else {
    Write-Host "2. Committing changes..."
    git commit -m $CommitMessage
}

# 기존 변경사항 Pull (선택 사항: 충돌 발생 시 수동 해결해야 할 수 있음)
Write-Host "3. Pulling latest from remote (rebase)..."
git pull origin main --rebase

# 서버에 푸시
Write-Host "4. Pushing to GitHub..."
git push origin main

if ($LASTEXITCODE -eq 0) {
    Write-Host "========== Sync Completed Successfully! ==========" -ForegroundColor Green
} else {
    Write-Host "========== Sync Failed! Check the error messages above ==========" -ForegroundColor Red
}

pause
