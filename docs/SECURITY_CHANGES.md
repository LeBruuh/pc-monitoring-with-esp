# Windows security hardening and migration

Agent version 5 keeps the CPU reader's elevated execution path separate from the
ordinary portable application. The installer copies its executable and DLLs to
the Windows Program Files folder under `EeveeMonitor/CpuSensors`, verifies owners
and write permissions, and rejects reparse-point installation paths. The task's
executable, working directory, and snapshot argument are absolute protected paths.

Administrators and SYSTEM can update the reader. Ordinary users have read/execute
access. Snapshots are atomically created with Administrators ownership and a
protected DACL: Administrators/SYSTEM may write, Users may read. They are placed
in the runtime's protected Data folder, with no automatic fallback to the old
user-writable snapshot. The tray application continues to run without elevation.

This addresses the previous local elevation opportunity where an unelevated
process could replace a privileged task's executable or DLLs in the portable
application directory. It does not claim to protect a system already controlled
by an administrator or to replace Windows updates and endpoint protection.

## Install the fix on each PC

1. Exit the old tray application before replacing its portable files.
2. Extract the complete version 5 package into its intended application directory.
3. Run `Installer_capteur_CPU.cmd` and approve Windows elevation. It recognizes and
   migrates the older named CPU task, waits for its old process to exit, then
   registers the protected action. An unexpected task action or unsafe target
   permissions cause an error rather than an insecure fallback.
4. Start `EeveeMonitor.exe`. Its diagnostic should report version 5 and the
   protected snapshot path under Program Files.

Updating source or merging the pull request alone does not migrate an existing
installation: run the new CPU installer on each computer. Each future reader
update also requires this explicit elevated installation step. Firmware 6 and
the ESP32 serial protocol are unchanged.

## Other changes

- Native pystray notifications replace win10toast, removing the legacy
  setuptools/pkg_resources version constraint.
- A fresh Windows build uses pip 26.2.2 and setuptools 84.2.1; the complete
  security-checked build snapshot is in `computer/requirements-windows.lock.txt`.
  No known dependency vulnerabilities were reported at the time of this check;
  re-audit when updating or rebuilding.
- The pystray requirement now names the actually published 0.19.5 release.
- NVIDIA's executable is located using Windows known-folder APIs and only
  standard system/NVIDIA installation paths, with no current-directory/PATH
  fallback. Subprocess arguments remain fixed and shell execution is disabled.
- Sprite XML generation uses defusedxml and explicit palette validation.

Validation includes 26 Python tests, C# package-selection/snapshot-ACL tests,
PowerShell ownership/write-rights/junction rejection tests, a clean dependency
audit, and a real migration on the Intel/RTX server. A non-elevated process was
denied both creating files in the installed reader directory and opening its
snapshot for writing, while live CPU temperature and CPU+GPU power remained
readable. The packaged agent resumed the ESP32 USB connection successfully.
