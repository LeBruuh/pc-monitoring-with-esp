param([string]$Python='python')
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$source=Join-Path $repoRoot 'computer'
$sensorDirectory=Join-Path $source 'sensors'
if(-not (Test-Path -LiteralPath (Join-Path $sensorDirectory 'CpuSensors.exe'))){throw 'Run Build-CpuSensors.ps1 first.'}
$workDirectory=Join-Path $repoRoot 'build\pyinstaller'
$distribution=Join-Path $repoRoot 'dist'
New-Item -ItemType Directory -Force -Path $workDirectory | Out-Null
& $Python -m PyInstaller --noconfirm --windowed --onedir --name EeveeMonitor --distpath $distribution --workpath $workDirectory --specpath $workDirectory --icon (Join-Path $source 'assets\eevee-icon.ico') --add-data ((Join-Path $source 'assets')+';assets') --hidden-import win32com.client --hidden-import win32timezone (Join-Path $source 'eeveemonitoring.py')
if($LASTEXITCODE -ne 0){throw 'Agent build failed.'}
$app=Join-Path $distribution 'EeveeMonitor'
$sensorDestination=Join-Path $app 'sensors'
New-Item -ItemType Directory -Force -Path $sensorDestination | Out-Null
Get-ChildItem -LiteralPath $sensorDirectory -File | Where-Object {$_.Extension -in '.exe','.dll','.cs'} | ForEach-Object {Copy-Item -LiteralPath $_.FullName -Destination $sensorDestination -Force}
foreach($name in @('Installer_capteur_CPU.cmd','Installer_capteur_CPU.ps1','SensorInstallSecurity.psm1')){Copy-Item -LiteralPath (Join-Path $source $name) -Destination $app -Force}
Copy-Item -LiteralPath (Join-Path $repoRoot 'docs\WINDOWS.md') -Destination (Join-Path $app 'LIRE_AVANT_UTILISATION.md') -Force
Write-Output ('Portable agent built in '+$app)
