
# Script to install Flutter SDK on Windows
# Run with: powershell -ExecutionPolicy Bypass -File .\install_flutter.ps1

$flutterUrl = "https://storage.googleapis.com/flutter_infra_release/releases/stable/windows/flutter_windows_3.19.0-stable.zip"
$destinationDir = "$env:USERPROFILE\src\flutter"
$zipFile = "$env:TEMP\flutter.zip"

Write-Host "Checking if Flutter is already installed..." -ForegroundColor Cyan
if (Test-Path "$destinationDir\bin\flutter.bat") {
    Write-Host "Flutter is already installed at $destinationDir" -ForegroundColor Yellow
    Write-Host "Please ensure $destinationDir\bin is in your PATH."
    exit
}

# Create destination directory
if (!(Test-Path -Path $destinationDir)) {
    New-Item -ItemType Directory -Force -Path $destinationDir | Out-Null
    Write-Host "Created directory: $destinationDir" -ForegroundColor Green
} else {
    # If directory exists but is empty/corrupt, we might want to warn
    Write-Host "Directory $destinationDir already exists." -ForegroundColor Yellow
}

# Download
Write-Host "Downloading Flutter SDK from $flutterUrl..." -ForegroundColor Cyan
try {
    Invoke-WebRequest -Uri $flutterUrl -OutFile $zipFile
} catch {
    Write-Host "Error downloading Flutter: $_" -ForegroundColor Red
    exit 1
}

# Extract
Write-Host "Extracting Flutter SDK to $destinationDir (This may take a few minutes)..." -ForegroundColor Cyan
try {
    # The zip contains a 'flutter' folder at root, so we extract to the parent of destinationDir if we want it exact,
    # or typically we extract to C:\src and it creates C:\src\flutter.
    # Our destinationDir is ...\src\flutter.
    
    # Let's extract to the PARENT directory so we don't get ...\src\flutter\flutter
    $extractPath = Split-Path -Parent $destinationDir
    if (!(Test-Path -Path $extractPath)) { New-Item -ItemType Directory -Force -Path $extractPath | Out-Null }
    
    Expand-Archive -Path $zipFile -DestinationPath $extractPath -Force
    Write-Host "Extraction complete." -ForegroundColor Green
} catch {
    Write-Host "Error extracting Flutter: $_" -ForegroundColor Red
    exit 1
}

# Cleanup
Remove-Item $zipFile -Force

# Add to PATH
$binPath = "$destinationDir\bin"
Write-Host "Adding $binPath to User Environment PATH..." -ForegroundColor Cyan

$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
if ($currentPath -notlike "*$binPath*") {
    $newPath = "$currentPath;$binPath"
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    Write-Host "Success! Added Flutter to PATH." -ForegroundColor Green
} else {
    Write-Host "Flutter bin is already in PATH." -ForegroundColor Yellow
}

Write-Host "`nInstallation Completed Successfully! 🚀" -ForegroundColor Green
Write-Host "IMPORTANT: You must RESTART your terminal/IDE for the 'flutter' command to work." -ForegroundColor Magenta
Write-Host "After restarting, run 'flutter doctor' to verify."
