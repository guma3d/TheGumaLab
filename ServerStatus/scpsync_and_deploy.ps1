$LocalPath = "C:\Users\guma3\OneDrive\Documents\TheGumaLab\ServerStatus"
$RemotePath = "d:/TheGumaLab/ServerStatus"
$SSHHost = "HomeServer"

Write-Host "Starting Direct Cleanup & Sync to $SSHHost..."

# 1. Clean Remote Garbage
# We explicitly remove the files that we deleted locally to ensure the server is clean.
# Be careful with wildcards.
$FilesRemove = "install_watchdog_admin.cmd start_watchdog.cmd monitor_lhm.ps1 check_sensors.py config.toml docker_config.json redeploy_server.cmd gpu_server.py requirements.txt start_gpu_agent.cmd install_gpu_agent.cmd"

Write-Host "Cleaning up old files on remote..."
# Using PowerShell on remote or cmd del. Remote is Windows.
# "del /Q file1 file2 ..." works in cmd.
ssh $SSHHost "cd /d $RemotePath && del /Q $FilesRemove"
# We ignore errors here in case files are already gone.

# 2. Copy Files (Direct SCP)
Write-Host "Copying core files..."
scp -r "$LocalPath\app.py" "${SSHHost}:${RemotePath}/app.py"
scp -r "$LocalPath\templates" "${SSHHost}:${RemotePath}/"
scp -r "$LocalPath\docker-compose.yml" "${SSHHost}:${RemotePath}/docker-compose.yml"
scp -r "$LocalPath\Dockerfile" "${SSHHost}:${RemotePath}/Dockerfile"

if ($LASTEXITCODE -eq 0) {
    Write-Host "Files Transferred Successfully."
    
    # 3. Trigger Rebuild
    Write-Host "Triggering Remote Rebuild..."
    ssh $SSHHost "cd /d $RemotePath && docker-compose down && docker-compose up -d --build"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Deployment Complete!"
    }
    else {
        Write-Host "Deployment Failed."
    }
}
else {
    Write-Host "File Transfer Failed."
}
