# proxmox-win-cloudinit
# Proxmox Windows Cloud-Init with Secure Password Management

## ⚠️ Project Notice
This project does not belong to us. The GitHub repository is a fork of [Gecko-IT](https://git.geco-it.net/GECO-IT-PUBLIC/Geco-Cloudbase-Init) which originated this project but is no longer maintained. We decided to maintain it and keep it up to date for current Proxmox versions.

## Overview

This is an enhanced implementation of Cloudbase-Init for Windows virtual machines running on Proxmox VE, featuring **secure password management** where passwords are encrypted in configuration files but decrypted for cloud-init delivery.

## Key Features

### 🔐 **Secure Password Handling (NEW)**
- **Encrypted storage**: Windows VM passwords are encrypted with AES encryption in `/etc/pve/qemu-server/<vmid>.conf`
- **Automatic decryption**: Passwords are decrypted when sent to cloud-init metadata for Windows VMs
- **Enhanced security**: Unlike the previous implementation, passwords are no longer stored in plain text

### 🚀 **Cloud-Init Capabilities**
Use Cloudbase-Init with Windows VMs to:
* Create a new user with username or enable administrator
* Set a password on the new user or administrator (**now with encryption**)
* Set static IP or DHCP on network adapters
* Set DNS on network adapters
* Automatic VM update on boot
* Enable RDP
* Set machine hostname
* Insert public SSH keys to "user/.ssh/authorized_keys" file
* Expand partition volumes automatically when disk is resized

## Implementation Details

### Modified Files
- **Qemu.pm**: Enhanced to encrypt Windows VM passwords using reversible AES encryption
- **Cloudinit.pm**: Enhanced to decrypt passwords before sending to cloud-init metadata
- **PasswordUtils.pm**: New module providing secure reversible encryption/decryption functions

### Password Storage Format
- **Windows VMs**: `encrypted-data>` (encrypted with AES)
- **Linux VMs**: Traditional bcrypt hash format (unchanged)

## Installation

### Prerequisites
⚠️ **Compatibility**: Tested and approved for Proxmox VE 8.2.2. Please backup both files before applying patches on other versions:
- `/usr/share/perl5/PVE/QemuServer/Cloudinit.pm`
- `/usr/share/perl5/PVE/API2/Qemu.pm`

Install required Perl modules:
```bash
apt-get update
apt-get install libcrypt-cbc-perl libcrypt-cipher-aes-perl libmime-base64-perl
```

### Automatic Patch Application

1. **Test patch compatibility:**
```bash
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/Qemu.pm.patch" --dry-run && echo "Qemu.pm patch can be applied" || echo "Can't apply Qemu.pm patch!"
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/Cloudinit.pm.patch" --dry-run && echo "Cloudinit.pm patch can be applied" || echo "Can't apply Cloudinit.pm patch!"
```

2. **If patches can't be applied, reinstall qemu-server:**
```bash
apt reinstall qemu-server
```

3. **Apply patches:**
```bash
# Install PasswordUtils module
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/PasswordUtils.pm.patch"

# Apply Qemu.pm patch
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/Qemu.pm.patch"

# Apply Cloudinit.pm patch
patch --force --forward --backup -p0 --directory / --input "/absolute/path/to/Cloudinit.pm.patch"
```

4. **Restart Proxmox services:**
```bash
systemctl restart pvedaemon
systemctl restart pveproxy
```

### Manual Installation

For manual installation instructions, see: [Manual Patching Guide](MANUALPATCH.md)

### Patch Reversal
```bash
patch --force --reverse --backup -p0 --directory / --input "/absolute/path/to/patchfile.pm.patch"
```
```sh
wget https://raw.githubusercontent.com/Pinous-Heberg/proxmox-win-cloudinit/main/proxmox-patch/checkupdate.sh -O /opt/checkupdate.sh
chmod +x /opt/checkupdate.sh
crontab -e
```
And add this in crontab :
```sh
0 5 * * * bash /opt/checkupdate.sh -y
```

## Windows VM Configuration
* Create a Windows VM in proxmox
* Go to Hardware section of your VM, add Cloud-Init Drive and Serial Port 0

### ⚠️ For non-server versions of Windows, please press CTRL + SHIFT + F3 when configuring the network and the user to switch to constructor mode, which will allow you to run the Sysprep at the end of this tutorial.

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
* Eject the cloud-init disk after all the steps performed at startup (optional).

Move those scripts into Cloudbase Solutions\Cloudbase-Init\LocalScripts\ in your program files of your Windows VM.

## If you were using the update script, please run these two commands before running the SysPrep:
### ⚠️ If you are running cloudbase-init on Windows Server 2016, please run these commands before running the commands to install "PSWindowsUpdate":
```ps1
Set-ItemProperty -Path ‘HKLM:\SOFTWARE\Wow6432Node\Microsoft\.NetFramework\v4.0.30319’ -Name ‘SchUseStrongCrypto’ -Value ‘1’ -Type DWord
Set-ItemProperty -Path ‘HKLM:\SOFTWARE\Microsoft\.NetFramework\v4.0.30319’ -Name ‘SchUseStrongCrypto’ -Value ‘1’ -Type DWord
```
```ps1
Install-Module PSWindowsUpdate -Force -AllowClobber
Import-Module PSWindowsUpdate
```


### ⚠️ If you have an error like below when you try to sysprep your windows server 2025 template you can try to running this commands and try again:
![](https://www.urtech.ca/wp-content/uploads/2018/07/syspre-setupact-log-error.jpg)
```ps1
Import-Module Appx
Import-Module Dism
Get-AppxPackage | Remove-AppxPackage
```

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
cd "C:\Program Files\Cloudbase Solutions\Cloudbase-Init\conf"
C:\Windows\System32\sysprep\sysprep.exe /generalize /oobe /unattend:Unattend.xml
```
