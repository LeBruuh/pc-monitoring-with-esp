using System.IO;
using System.Security.AccessControl;
using System.Security.Principal;
using System.Text;

public static class SensorFileSecurity {
 public static FileSecurity SnapshotAcl() {
  var acl=new FileSecurity();
  acl.SetAccessRuleProtection(true,false);
  var administrators=new SecurityIdentifier(WellKnownSidType.BuiltinAdministratorsSid,null);
  acl.SetOwner(administrators);
  acl.AddAccessRule(new FileSystemAccessRule(administrators,FileSystemRights.FullControl,AccessControlType.Allow));
  acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(WellKnownSidType.LocalSystemSid,null),FileSystemRights.FullControl,AccessControlType.Allow));
  acl.AddAccessRule(new FileSystemAccessRule(new SecurityIdentifier(WellKnownSidType.BuiltinUsersSid,null),FileSystemRights.Read,AccessControlType.Allow));
  return acl;
 }
 public static void WriteNew(string path,string text) {
  // Apply owner and DACL at creation, before publishing even a temporary file.
  using(var file=new FileStream(path,FileMode.CreateNew,FileSystemRights.Write,FileShare.None,4096,FileOptions.None,SnapshotAcl()))
  using(var writer=new StreamWriter(file,new UTF8Encoding(false))) writer.Write(text);
 }
}
