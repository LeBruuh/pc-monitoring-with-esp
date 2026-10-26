param(
 [string]$ArduinoCli='arduino-cli',
 [string]$ConfigFile,
 [string]$BuildPath
)
$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$setup=Join-Path $repoRoot 'arduino\libraries\TFT_eSPI\User_Setup.h'
$sketch=Join-Path $repoRoot 'arduino\script'
$output=Join-Path $repoRoot 'build\firmware'
if(-not $BuildPath){$BuildPath=Join-Path $repoRoot 'build\arduino'}
$arguments=@()
if($ConfigFile){$arguments+=@('--config-file',$ConfigFile)}
$flags='-DUSER_SETUP_LOADED -include "'+$setup+'"'
$arguments+=@('compile','--fqbn','esp32:esp32:nodemcu-32s','--build-path',$BuildPath,'--output-dir',$output,'--build-property',('compiler.cpp.extra_flags='+$flags),'--build-property',('compiler.c.extra_flags='+$flags),$sketch)
& $ArduinoCli @arguments
if($LASTEXITCODE -ne 0){throw 'Firmware build failed.'}
Write-Output ('Firmware built in '+$output)
