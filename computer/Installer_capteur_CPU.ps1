param()
$ErrorActionPreference='Stop'
if(-not [Environment]::Is64BitProcess){throw 'Use the 64-bit Windows PowerShell installer.'}
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=New-Object Security.Principal.WindowsPrincipal($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){
 $powershell=Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::System)) 'WindowsPowerShell\v1.0\powershell.exe'
 $child=Start-Process -FilePath $powershell -Verb RunAs -WindowStyle Hidden -ArgumentList @('-NoProfile','-ExecutionPolicy','Bypass','-File',('"'+$PSCommandPath+'"')) -PassThru -Wait
 exit $child.ExitCode
}
Import-Module (Join-Path $PSScriptRoot 'SensorInstallSecurity.psm1') -Force
$taskName='ESP32Monitor-CPU-Temperature'
$sourceBase=if(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'agent\EeveeMonitor\EeveeMonitor.exe')){Join-Path $PSScriptRoot 'agent\EeveeMonitor'}else{$PSScriptRoot}
$sourceSensors=Join-Path $sourceBase 'sensors'
foreach($name in @('CpuSensors.exe','LibreHardwareMonitorLib.dll')){
 if(-not (Test-Path -LiteralPath (Join-Path $sourceSensors $name))){throw ('Missing CPU reader component: '+$name)}
}
$programFiles=[Environment]::GetFolderPath([Environment+SpecialFolder]::ProgramFiles)
Assert-ProtectedItem -LiteralPath $programFiles
if(-not (Test-Path -LiteralPath (Join-Path $programFiles 'PawnIO\PawnIOLib.dll'))){throw 'Install the official PawnIO driver before installing the CPU reader.'}
$installRoot=Join-Path $programFiles 'EeveeMonitor'
$runtime=Join-Path $installRoot 'CpuSensors'
$dataDirectory=Join-Path $runtime 'Data'
$executable=Join-Path $runtime 'CpuSensors.exe'
$snapshot=Join-Path $dataDirectory 'cpu-sensors.json'
$oldTask=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if($oldTask){
 if($oldTask.Actions.Count -ne 1){throw 'Unexpected existing CPU task actions.'}
 $oldExecutable=$oldTask.Actions[0].Execute
 $oldDirectory=[IO.Path]::GetDirectoryName($oldExecutable)
 $oldBase=[IO.Path]::GetDirectoryName($oldDirectory)
 $legacy=([IO.Path]::GetFileName($oldExecutable) -eq 'CpuSensors.exe' -and [IO.Path]::GetFileName($oldDirectory) -eq 'sensors' -and ((Test-Path -LiteralPath (Join-Path $oldBase 'EeveeMonitor.exe')) -or (Test-Path -LiteralPath (Join-Path $oldBase 'eeveemonitoring.py'))))
 if($oldExecutable -ne $executable -and -not $legacy){throw 'Existing CPU task points to an unexpected program; refusing to replace it.'}
}
if($oldTask){
 $processes=@(Get-Process -Name CpuSensors -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $oldExecutable})
 Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
 foreach($process in $processes){if(-not $process.WaitForExit(15000)){throw 'Previous CPU reader did not exit.'}}
}
foreach($directory in @($installRoot,$runtime,$dataDirectory)){Initialize-ProtectedDirectory -LiteralPath $directory}
foreach($file in Get-ChildItem -LiteralPath $sourceSensors -File | Where-Object {$_.Name -eq 'CpuSensors.exe' -or $_.Extension -eq '.dll'}){
 if(($file.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Linked files are not accepted as CPU reader components.'}
 $destination=Join-Path $runtime $file.Name
 Copy-Item -LiteralPath $file.FullName -Destination $destination -Force -ErrorAction Stop
 Set-ProtectedFileAcl -LiteralPath $destination
}
Assert-ProtectedItem -LiteralPath $runtime -Recurse
$action=New-ScheduledTaskAction -Execute $executable -Argument ('"'+$snapshot+'"') -WorkingDirectory $runtime
$trigger=New-ScheduledTaskTrigger -AtLogOn -User $identity.Name
$taskPrincipal=New-ScheduledTaskPrincipal -UserId $identity.Name -LogonType Interactive -RunLevel Highest
$settings=New-ScheduledTaskSettingsSet -Priority 4 -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Principal $taskPrincipal -Settings $settings -Description 'CPU-only sensor reader in an administrator-protected installation; local read-only measurements for EeveeMonitor.' -Force -ErrorAction Stop | Out-Null
Start-ScheduledTask -TaskName $taskName -ErrorAction Stop
Write-Output ('Protected CPU reader installed: '+$executable)
