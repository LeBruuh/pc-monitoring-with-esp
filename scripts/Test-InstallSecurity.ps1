$ErrorActionPreference='Stop'
$repoRoot=Split-Path -Parent $PSScriptRoot
Import-Module (Join-Path $repoRoot 'computer\SensorInstallSecurity.psm1') -Force
$safe=New-ProtectedAcl -Directory
if(-not (Test-TrustedAcl $safe)){throw 'Secure ACL was rejected.'}
$users=New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')
foreach($rights in @([Security.AccessControl.FileSystemRights]::WriteData,[Security.AccessControl.FileSystemRights]::Delete,[Security.AccessControl.FileSystemRights]::ChangePermissions,[Security.AccessControl.FileSystemRights]::TakeOwnership)){
 $unsafe=New-ProtectedAcl -Directory
 $unsafe.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($users,$rights,[Security.AccessControl.AccessControlType]::Allow)))
 if(Test-TrustedAcl $unsafe){throw ('Unsafe write right was accepted: '+$rights)}
}
$ownerAcl=New-ProtectedAcl -Directory
$ownerAcl.SetOwner((New-Object Security.Principal.SecurityIdentifier('S-1-5-21-111-222-333-1001')))
if(Test-TrustedAcl $ownerAcl){throw 'Unprivileged owner was accepted.'}
$build=Join-Path $repoRoot 'build\tests'
New-Item -ItemType Directory -Force -Path $build | Out-Null
$junction=Join-Path $build 'rejected-junction'
$target=Join-Path $build 'junction-target'
New-Item -ItemType Directory -Force -Path $target | Out-Null
if(-not (Test-Path -LiteralPath $junction)){New-Item -ItemType Junction -Path $junction -Target $target | Out-Null}
$reparseRejected=$false
try {Assert-ProtectedItem -LiteralPath $junction} catch {if($_.ToString() -like '*Reparse points*'){$reparseRejected=$true}else{throw}}
if(-not $reparseRejected){throw 'Junction was not rejected.'}
$compiler=Join-Path ([Environment]::GetFolderPath([Environment+SpecialFolder]::Windows)) 'Microsoft.NET\Framework64\v4.0.30319\csc.exe'
$test=Join-Path $build 'TestSnapshotAcl.exe'
& $compiler /nologo /target:exe ('/out:'+$test) (Join-Path $repoRoot 'computer\sensors\SensorFileSecurity.cs') (Join-Path $repoRoot 'tests\test_snapshot_acl.cs')
if($LASTEXITCODE -ne 0){throw 'Snapshot ACL test build failed.'}
& $test
if($LASTEXITCODE -ne 0){throw 'Snapshot ACL test failed.'}
Write-Output 'PASS: safe ACL accepted; unprivileged ownership and dangerous writes rejected.'
