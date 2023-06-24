# proxmox-win-cloudinit
## ⚠️This project doesn't belong to me. The github repository is just a fork of [Gecko-IT](https://git.geco-it.net/GECO-IT-PUBLIC/Geco-Cloudbase-Init) which is at the origin of this project but which doesn't keep it up to date anymore, that's why I decided to keep it up to date with proxmox v8 which has just been released.
This is an implementation of Cloudbase-Init to Windows virtual machines running in a Proxmox Node in order to use cloud-init with those vms.

What can you do with this implementation?
Use Cloudbase-Init with Windows VMs to:
* Create a new user with username or enable administrator.
* Set a password on the new user or administrator.
* Set static ip or dhcp on network adapters.
* Set DNS on network adapters.
* Automatic VM update on boot
* Set machine hostname.
* Insert public ssh keys to "user/.ssh/authorized_keys" file of created/enabled user.
* Expand partition volumes automatically when there's a resized disk.

You can do all below on system startup with the data provided by the cloud-init section of the proxmox gui.


There is two files that we need to modify Qemu.pm and Cloudinit.pm.
* Qemu.pm to get password as cleartext in meta_data drive when it is a Windows VM.
* Cloudinit.pm to generate a metadata json file with variables that are compatible with Cloudbase-Init.

## Install Proxmox patch

### ⚠️ The patch has been tested and approved for proxmox version 8.0.3 please make a backup of both Cloudinit.pm stored in ```/usr/share/perl5/PVE/QemuServer/Cloudinit.pm``` and Qemu.pm stored in ```/usr/share/perl5/PVE/API2/Qemu.pm``` if you are trying to apply the patch in a version prior to proxmox 8.0.3 or higher.

## Launch below as a test to see if you can apply the patch file, change path to where you downloaded the files and run this for two .patch files.
```sh
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/patchfile.pm.patch" --dry-run && echo "You can apply patch" || { echo "Can't apply patch!";}
```

## If the result is "Can't apply patch!", you can type "apt reinstall qemu-server" to reinstall the qemu-server files(If you have made changes to qemu-server source files they will be lost!)

## Apply the patch if the result is "You can apply patch"
```sh
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/patchfile.pm.patch"
```
If you want to revert the patch:
```sh
patch --force --reverse --backup -p0 --directory / --input "/absolute/path/to/patchfile.pm.patch"
```

If you want to apply the patch manually you can follow these steps: [Manual Patching](https://github.com/codding-nepale/proxmox-win-cloudinit/blob/main/MANUALPATCH.md)

## Windows VM Configuration
* Create a Windows VM in proxmox
* Go to Hardware section of your VM, add Cloud-Init Drive and Serial Port 0

Then configure Windows to your needs and proceed to Cloudbase-Init installation.

### Install Cloudbase-Init
Install Cloudbase-Init Continous Build from the [official website](https://cloudbase.it/cloudbase-init/#download).

Why Continous Build? Because the stable build dates from 2020 and doesn't include functionalities we use.

### Cloudbase-Init LocalScripts
We have [five scripts](https://github.com/codding-nepale/proxmox-win-cloudinit/tree/main/localscripts) that do some fonctionality that Cloudbase-Init doesnt have;
* Enabling administrator user when it's name is given to the Cloudbase-Init.
* Enabling DHCP on the network adapters.
* Update the dns with those set in the cloud-init configuration
* Update the system on startup (may slow down VM startup time)
* Eject the cloud-init disk after all the steps performed at startup.

## If you were using the update script, please run these two commands before running the SysPrep:
```ps1
Install-Module PSWindowsUpdate -Force -AllowClobber
Import-Module PSWindowsUpdate
```
Move those scripts into Cloudbase Solutions\Cloudbase-Init\LocalScripts\ in your program files of your Windows VM.


### Configure Cloudbase-Init
Deploy [these two conf files](https://github.com/codding-nepale/proxmox-win-cloudinit/tree/main/conf) to `C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf`.

Inside those files you will find the default Administrator name and the user group that will be used while user creation. You can launch our [ModifyConf.ps1](https://github.com/codding-nepale/proxmox-win-cloudinit/tree/main/powershell) script to modify that file to get the correct username and group of your Windows language.

### Run PowerShell Script
[This](https://github.com/codding-nepale/proxmox-win-cloudinit/tree/main/powershell) powershell script has a few uses.
* Deletes the "cloudbase-init" user, delegates "cloudbase-init" service to local Systeme user and modifies execution path of the script also to use local system user.
* Installs OpenSSH-Server from optional features of Windows.
* Removes a store language package that causes an error when generelazing for sysprep.

Run this script after installing and configuring Cloudbase-Init Continous Build.

### Run SysPrep
When everything is installed simply run below in powershell to launch sysprep:

```sh
cd ‘C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf’
C:\Windows\System32\sysprep\sysprep.exe /generalize /oobe /unattend:Unattend.xml
```
