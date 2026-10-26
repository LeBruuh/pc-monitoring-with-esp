param()
$ErrorActionPreference='Stop'
$taskName='ESP32Monitor-CPU-Temperature'
$taskBase=if(Test-Path -LiteralPath (Join-Path $PSScriptRoot 'agent/EeveeMonitor/EeveeMonitor.exe')){
 Join-Path $PSScriptRoot 'agent/EeveeMonitor'
} elseif((Test-Path -LiteralPath (Join-Path $PSScriptRoot 'EeveeMonitor.exe')) -or (Test-Path -LiteralPath (Join-Path $PSScriptRoot 'eeveemonitoring.py'))){
 $PSScriptRoot
} else {throw 'Le dossier du moniteur est introuvable.'}
$taskExe=Join-Path $taskBase 'sensors/CpuSensors.exe'
$taskData=Join-Path $taskBase 'cpu-sensors.json'
if(-not (Test-Path -LiteralPath $taskExe)){throw 'Le lecteur CPU est absent du paquet.'}
if(-not (Test-Path -LiteralPath (Join-Path $env:ProgramFiles 'PawnIO/PawnIOLib.dll'))){
 throw 'PawnIO doit etre installe depuis son site officiel pour acceder aux capteurs CPU. Ne pas desactiver les protections Windows.'
}
$taskUser=[Security.Principal.WindowsIdentity]::GetCurrent().Name
$taskOld=Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if($taskOld -and $taskOld.Actions[0].Execute -ne $taskExe){
 throw 'Une tache du meme nom utilise un autre emplacement. Verifier avant de la remplacer.'
}
$taskAction=New-ScheduledTaskAction -Execute $taskExe -Argument ('"'+$taskData+'"') -WorkingDirectory (Split-Path -LiteralPath $taskExe)
$taskTrigger=New-ScheduledTaskTrigger -AtLogOn -User $taskUser
$taskPrincipal=New-ScheduledTaskPrincipal -UserId $taskUser -LogonType Interactive -RunLevel Highest
$taskSettings=New-ScheduledTaskSettingsSet -Priority 4 -ExecutionTimeLimit ([TimeSpan]::Zero) -MultipleInstances IgnoreNew -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
if($taskOld){
 # A running task keeps its old process priority until it is restarted.
 $taskProcesses=@(Get-Process -Name CpuSensors -ErrorAction SilentlyContinue | Where-Object {$_.Path -eq $taskExe})
 Stop-ScheduledTask -TaskName $taskName -ErrorAction Stop
 foreach($taskProcess in $taskProcesses){
  if(-not $taskProcess.WaitForExit(15000)){throw 'Le lecteur CPU precedent ne se termine pas. Reessayer apres sa fermeture.'}
 }
}
Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTrigger -Principal $taskPrincipal -Settings $taskSettings -Description 'Lecture CPU seule via LibreHardwareMonitor, sans serveur reseau ; donnees locales pour le moniteur ESP32.' -Force | Out-Null
Start-ScheduledTask -TaskName $taskName
Write-Output "Lecture CPU automatique configuree pour $taskUser."
