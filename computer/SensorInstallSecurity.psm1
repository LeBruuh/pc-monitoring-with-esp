$script:Administrators='S-1-5-32-544'
$script:System='S-1-5-18'
$script:Users='S-1-5-32-545'
$script:TrustedInstaller='S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464'
$script:Writers=@($script:Administrators,$script:System,$script:TrustedInstaller)
$script:WriteMask=[Security.AccessControl.FileSystemRights]::WriteData -bor [Security.AccessControl.FileSystemRights]::AppendData -bor [Security.AccessControl.FileSystemRights]::WriteExtendedAttributes -bor [Security.AccessControl.FileSystemRights]::WriteAttributes -bor [Security.AccessControl.FileSystemRights]::Delete -bor [Security.AccessControl.FileSystemRights]::DeleteSubdirectoriesAndFiles -bor [Security.AccessControl.FileSystemRights]::ChangePermissions -bor [Security.AccessControl.FileSystemRights]::TakeOwnership

function Test-TrustedAcl {
 param([Parameter(Mandatory=$true)]$Acl)
 if($Acl.GetOwner([Security.Principal.SecurityIdentifier]).Value -notin $script:Writers){return $false}
 foreach($rule in $Acl.GetAccessRules($true,$true,[Security.Principal.SecurityIdentifier])){
  if(($rule.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) -ne 0){continue}
  if($rule.AccessControlType -eq [Security.AccessControl.AccessControlType]::Allow -and
     ($rule.FileSystemRights -band $script:WriteMask) -ne 0 -and
     $rule.IdentityReference.Value -notin $script:Writers){return $false}
 }
 return $true
}

function Assert-ProtectedItem {
 param([Parameter(Mandatory=$true)][string]$LiteralPath,[switch]$Recurse)
 $item=Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop
 if(($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw ('Reparse points are not accepted in the elevated installation: '+$LiteralPath)}
 if(-not (Test-TrustedAcl (Get-Acl -LiteralPath $LiteralPath -ErrorAction Stop))){throw ('Unsafe owner or write permissions; refusing elevated installation: '+$LiteralPath)}
 if($Recurse -and $item.PSIsContainer){
  foreach($child in Get-ChildItem -LiteralPath $LiteralPath -Force -ErrorAction Stop){Assert-ProtectedItem -LiteralPath $child.FullName -Recurse}
 }
}

function New-ProtectedAcl {
 param([switch]$Directory)
 $acl=if($Directory){New-Object Security.AccessControl.DirectorySecurity}else{New-Object Security.AccessControl.FileSecurity}
 $acl.SetAccessRuleProtection($true,$false)
 $acl.SetOwner((New-Object Security.Principal.SecurityIdentifier($script:Administrators)))
 foreach($sid in @($script:Administrators,$script:System,$script:Users)){
  $rights=if($sid -eq $script:Users){[Security.AccessControl.FileSystemRights]::ReadAndExecute}else{[Security.AccessControl.FileSystemRights]::FullControl}
  $identity=New-Object Security.Principal.SecurityIdentifier($sid)
  $rule=if($Directory){New-Object Security.AccessControl.FileSystemAccessRule($identity,$rights,([Security.AccessControl.InheritanceFlags]::ContainerInherit -bor [Security.AccessControl.InheritanceFlags]::ObjectInherit),[Security.AccessControl.PropagationFlags]::None,[Security.AccessControl.AccessControlType]::Allow)}else{New-Object Security.AccessControl.FileSystemAccessRule($identity,$rights,[Security.AccessControl.AccessControlType]::Allow)}
  $acl.AddAccessRule($rule)
 }
 return $acl
}

function Initialize-ProtectedDirectory {
 param([Parameter(Mandatory=$true)][string]$LiteralPath)
 if(Test-Path -LiteralPath $LiteralPath){Assert-ProtectedItem -LiteralPath $LiteralPath -Recurse}
 else {
  Assert-ProtectedItem -LiteralPath ([IO.Path]::GetDirectoryName($LiteralPath))
  New-Item -ItemType Directory -Path $LiteralPath -ErrorAction Stop | Out-Null
 }
 Set-Acl -LiteralPath $LiteralPath -AclObject (New-ProtectedAcl -Directory) -ErrorAction Stop
 Assert-ProtectedItem -LiteralPath $LiteralPath
}

function Set-ProtectedFileAcl {
 param([Parameter(Mandatory=$true)][string]$LiteralPath)
 $item=Get-Item -LiteralPath $LiteralPath -Force -ErrorAction Stop
 if($item.PSIsContainer -or ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'Expected a regular installation file.'}
 Set-Acl -LiteralPath $LiteralPath -AclObject (New-ProtectedAcl) -ErrorAction Stop
 Assert-ProtectedItem -LiteralPath $LiteralPath
}

Export-ModuleMember -Function Test-TrustedAcl,Assert-ProtectedItem,Initialize-ProtectedDirectory,Set-ProtectedFileAcl,New-ProtectedAcl
