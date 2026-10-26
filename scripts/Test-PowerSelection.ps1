$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
$build=Join-Path $repoRoot 'build\tests'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$compiler=Join-Path $env:SystemRoot 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$test=Join-Path $build 'TestPowerSelection.exe'
& $compiler /nologo /target:exe ('/out:'+$test) (Join-Path $repoRoot 'computer\sensors\PowerSelection.cs') (Join-Path $repoRoot 'tests\test_power_selection.cs')
if($LASTEXITCODE -ne 0){throw 'Power-selection test build failed.'}
& $test
if($LASTEXITCODE -ne 0){throw 'Power-selection tests failed.'}
