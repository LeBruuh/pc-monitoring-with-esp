using System;
using System.Security.AccessControl;
using System.Security.Principal;
class SnapshotAclTests {
 static int Main() {
  var acl=SensorFileSecurity.SnapshotAcl();
  if(!acl.AreAccessRulesProtected || acl.GetOwner(typeof(SecurityIdentifier)).Value!="S-1-5-32-544") return 1;
  var rules=acl.GetAccessRules(true,true,typeof(SecurityIdentifier));
  if(rules.Count!=3) return 2;
  foreach(FileSystemAccessRule rule in rules) {
   string sid=rule.IdentityReference.Value;
   if(rule.AccessControlType!=AccessControlType.Allow) return 3;
   if(sid=="S-1-5-32-545") {
    if((rule.FileSystemRights & (FileSystemRights.WriteData|FileSystemRights.AppendData|FileSystemRights.Delete|FileSystemRights.ChangePermissions|FileSystemRights.TakeOwnership))!=0) return 4;
   } else if(sid!="S-1-5-18" && sid!="S-1-5-32-544") return 5;
  }
  Console.WriteLine("PASS: snapshot owner is Administrators; only Administrators/SYSTEM write; Users read.");
  return 0;
 }
}
