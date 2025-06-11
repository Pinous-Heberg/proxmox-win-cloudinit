## Manual Patching Instructions

# Manual Patch Instructions for Proxmox Windows Cloud-Init Support

This document provides step-by-step instructions for manually applying the patches to enable Windows cloud-init support with secure password handling in Proxmox VE.

## Overview

The patches implement:
1. **Encrypted password storage** for Windows VMs in configuration files
2. **Password decryption** for cloud-init metadata delivery to Windows VMs
3. **Secure reversible encryption** using AES encryption for Windows VM passwords

## Prerequisites

Ensure you have the required Perl modules installed:
```bash
apt-get update
apt-get install libcrypt-cbc-perl libcrypt-cipher-aes-perl libmime-base64-perl
```

## Installation Steps

### 1. Install PasswordUtils Module

Download and install the new password utilities module:

**File Location:** `/usr/share/perl5/PVE/QemuServer/PasswordUtils.pm`

```bash
# Download the PasswordUtils module directly from the repository
wget https://raw.githubusercontent.com/Pinous-Heberg/proxmox-win-cloudinit/main/proxmox-patch/sourcefiles/PasswordUtils.pm -O /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm

# Set proper ownership and permissions
chown root:root /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
chmod 644 /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
```

**Alternative method (if you have the local file):**
```bash
cp proxmox-patch/sourcefiles/PasswordUtils.pm /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
chown root:root /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
chmod 644 /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
```

### 2. Patch Qemu.pm

**File Location:** `/usr/share/perl5/PVE/API2/Qemu.pm`

#### 2.1 Add PasswordUtils Import

After the line:
```perl
use PVE::QemuServer::CPUConfig;
```

Add:
```perl
use PVE::QemuServer::PasswordUtils;
```

#### 2.2 Update Password Handling Logic

Find the section around line 2245 that contains:
```perl
} elsif ($opt eq 'cipassword') {
    # Same logic as in cloud-init (but with the regex fixed...)
    $param->{cipassword} = PVE::Tools::encrypt_pw($param->{cipassword})
        if $param->{cipassword} !~ /^\$(?:[156]|2[ay])(\$.+){2}/;
    $conf->{cipassword} = $param->{cipassword};
```

Replace it with:
```perl
} elsif ($opt eq 'cipassword') {
    if (PVE::QemuServer::Helpers::windows_version($conf->{ostype})) {
        # For Windows VMs, use reversible encryption
        $param->{cipassword} = PVE::QemuServer::PasswordUtils::encrypt_pw_reversible($param->{cipassword})
            if $param->{cipassword} !~ /^\$5\$/;
    } else {
        # Same logic as in cloud-init (but with the regex fixed...)
        $param->{cipassword} = PVE::Tools::encrypt_pw($param->{cipassword})
            if $param->{cipassword} !~ /^\$(?:[156]|2[ay])(\$.+){2}/;
    }
    $conf->{cipassword} = $param->{cipassword};
```

### 3. Patch Cloudinit.pm

**File Location:** `/usr/share/perl5/PVE/QemuServer/Cloudinit.pm`

#### 3.1 Add PasswordUtils Import

After the line:
```perl
use PVE::QemuServer::Helpers;
```

Add:
```perl
use PVE::QemuServer::PasswordUtils;
```

#### 3.2 Update Windows Metadata Generation

Find the section around line 324 in the `cloudbase_configdrive2_metadata` function:
```perl
$meta_data->{'admin_pass'} = $conf->{cipassword} if $conf->{cipassword};
```

Replace it with:
```perl
# For Windows VMs, decrypt the password before sending to cloud-init
if ($conf->{cipassword}) {
    if ($conf->{cipassword} =~ /^\$5\$/) {
        $meta_data->{'admin_pass'} = PVE::QemuServer::PasswordUtils::decrypt_pw_reversible($conf->{cipassword});
    } else {
        $meta_data->{'admin_pass'} = $conf->{cipassword};
    }
}
```

## Automatic Patch Application

Alternatively, you can apply the patches automatically using the provided patch files:

```bash
# Apply Qemu.pm patch
cd /usr/share/perl5/PVE/API2/
cp Qemu.pm Qemu.pm.backup
patch -p1 < /path/to/proxmox-patch/Qemu.pm.patch

# Install PasswordUtils module
patch -p1 < /path/to/proxmox-patch/PasswordUtils.pm.patch

# Apply Cloudinit.pm patch  
cd /usr/share/perl5/PVE/QemuServer/
cp Cloudinit.pm Cloudinit.pm.backup
patch -p1 < /path/to/proxmox-patch/Cloudinit.pm.patch
```

## Verification

After applying the patches:

1. **Restart Proxmox services:**
   ```bash
   systemctl restart pveproxy
   systemctl restart pvedaemon
   ```

2. **Test with a Windows VM:**
   - Create or edit a Windows VM
   - Set a cloud-init password
   - Verify the password is stored with `/^\$5\$/` prefix in `/etc/pve/qemu-server/<vmid>.conf`
   - Start the VM and verify the password is correctly applied

3. **Check for syntax errors:**
   ```bash
   perl -c /usr/share/perl5/PVE/API2/Qemu.pm
   perl -c /usr/share/perl5/PVE/QemuServer/Cloudinit.pm  
   perl -c /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
   ```

## Security Notes

- Passwords for Windows VMs are now encrypted in configuration files using AES encryption
- The encryption key is derived from system-specific data
- For production use, consider implementing a more secure key management system
- Non-Windows VMs continue to use the existing bcrypt-based password hashing

## Troubleshooting

- If you encounter module loading errors, ensure all required Perl dependencies are installed
- Check Proxmox logs: `/var/log/pveproxy/access.log` and `/var/log/daemon.log`
- Verify file permissions are correct (644 for .pm files, root:root ownership)
- Test password encryption/decryption manually using the PasswordUtils module functions
   $default_dns = $nameservers; # Windows support
   ```

3. Add the following code after:
   ```perl5
   if ($searchdomains && @$searchdomains) {
       $searchdomains = join(' ', @$searchdomains);
       $content .= " dns_search $searchdomains\n";
   ```
   Add:
   ```perl5
   $default_search = $searchdomains; # Windows support
   ```

4. Add the DNS configuration to the network configuration file:
   ```perl5
   if(PVE::QemuServer::windows_version($ostype) && not($dnsinserted)) {
       $content .= " dns-nameservers $default_dns\n";
       $content .= " dns-search $default_search\n";
       $dnsinserted++;
   }
   ```

5. Add the `get_mac_addresses` function after `configdrive2_network`:
   ```perl5
   sub get_mac_addresses {
       # Function code
   }
   ```

6. Replace:
   ```perl5
   my ($user, $network) = @_ ;
   ```
   With:
   ```perl5
   my ($conf, $vmid, $user, $network) = @_ ;
   ```

7. Replace:
   ```perl5
   return configdrive2_metadata($uuid_str) ;
   ```
   With:
   ```perl5
   return configdrive2_metadata($conf, $vmid, $user, $network);
   ```

8. Replace:
   ```perl5
   my ($uuid) = @_;
   ```
   With:
   ```perl5
   my ($password, $uuid, $hostname, $username, $pubkeys, $network, $dhcpmacs) = @_;
   ```

9. Replace:
   ```perl5
   "uuid": "$uuid",
   "network_config": { "content_path": "/content/0000" }
   ```
   With:
   ```perl5
   "meta":{
       "admin_pass": "$password"$username
   },
   "uuid":"$uuid",
   "hostname":"$hostname",
   "network_config":{"content_path":"/content/0000"}$pubkeys$dhcpmacs
   ```

10. Replace:
    ```perl5
    $meta_data = configdrive2_gen_metadata($user_data, $network_data);
    ```
    With:
    ```perl5
    $meta_data = configdrive2_gen_metadata($conf, $vmid, $user_data, $network_data);
    ```

## Troubleshooting and Reversal

### Complete Removal (Uninstallation)

If you need to completely remove the patches and revert to the original functionality:

1. **Remove PasswordUtils module:**
```bash
rm -f /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
```

2. **Restore original files from backups:**
```bash
# If you have .orig backup files from patching
cp /usr/share/perl5/PVE/API2/Qemu.pm.orig /usr/share/perl5/PVE/API2/Qemu.pm
cp /usr/share/perl5/PVE/QemuServer/Cloudinit.pm.orig /usr/share/perl5/PVE/QemuServer/Cloudinit.pm
```

3. **Or reinstall qemu-server package:**
```bash
apt reinstall qemu-server
```

4. **Restart Proxmox services:**
```bash
systemctl restart pvedaemon
systemctl restart pveproxy
```

### Verification

After installation, verify that the modules are properly loaded:

```bash
# Check if PasswordUtils module exists and is readable
ls -la /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm

# Test Perl syntax
perl -c /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm
perl -c /usr/share/perl5/PVE/API2/Qemu.pm
perl -c /usr/share/perl5/PVE/QemuServer/Cloudinit.pm

# Check Proxmox services status
systemctl status pvedaemon
systemctl status pveproxy
```

### Common Issues

1. **"Can't locate PasswordUtils.pm" error:**
   - Ensure the file is in the correct location: `/usr/share/perl5/PVE/QemuServer/PasswordUtils.pm`
   - Check file permissions: `chmod 644 /usr/share/perl5/PVE/QemuServer/PasswordUtils.pm`

2. **Perl syntax errors:**
   - Verify all manual edits were applied correctly
   - Check for missing commas, brackets, or semicolons
   - Use `perl -c filename.pm` to check syntax

3. **Service restart failures:**
   - Check logs: `journalctl -u pvedaemon -u pveproxy`
   - Verify all files have correct syntax
   - Ensure all required Perl modules are installed
