#!/bin/bash

version_file="/var/tmp/qemu-server-vers"

cloudinit_path="/usr/share/perl5/PVE/QemuServer/Cloudinit.pm"

qemu_path="/usr/share/perl5/PVE/API2/Qemu.pm"

current_version=$(apt show qemu-server 2>/dev/null | grep "Version" | awk '{print $2}')

log_file="/var/log/qemu-server.log"

if [ ! -f "$version_file" ]; then
    touch "$version_file"
    echo "$current_version" > "$version_file"
    echo "Created version file: $version_file" >> $log_file
    exit 0
fi

saved_version=$(cat "$version_file")

function check_if_is_pve() {
    kernel=$(uname -r)
    if [[ $kernel == *"pve"* ]]; then
        echo 0
    else
        echo 1
    fi
}

function warning() {
    if [[ ! $1 == "-y" ]]; then
        read -p "Warning: This script is restarting the pveproxy service to apply the patch please execute in SSH as root only. Do you want to continue? [Y/n] " -r
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            echo 0
        elif [[ $REPLY =~ ^[Nn]$ ]]; then
            echo 1
        elif [[ $REPLY == "" ]]; then
            echo 0
        else
            echo 1
        fi
    fi
}

function main() {
    warning
    if [ "$(check_if_is_pve)" == "1" ]; then
        echo "You are not running on PVE. Exiting..." >> $log_file
        exit 1
    fi

    if [ "$current_version" != "$saved_version" ]; then
        echo "$current_version" > "$version_file" 2>/dev/null

        download_latest_version
            echo "Download complete. Verifying patch compatibility..." >> $log_file

        if [ -f /tmp/Cloudinit.pm.patch ] && [ -f /tmp/Qemu.pm.patch ]; then
            if ! command -v patch &> /dev/null
            then
                echo "patch is not installed. Installing..." >> $log_file
                apt install patch -y
            fi

            if [ "$(check_patch_compatibility)" == "0" ]; then
                echo "Patch is compatible. Backup original files and applying patch..." >> $log_file
                backup_original_files
                apply_patch
            else
                echo "Verification failed. Can't apply patch! Please wait until the patch is compatible with your version of Qemu Server. Exiting..." >> $log_file
                exit 1
            fi
        fi
    else
        exit 0
    fi
}

function download_latest_version() {
    if ! command -v wget &> /dev/null
    then
        echo "wget is not installed. Installing..." >> $log_file
        apt install wget -y
    fi

    echo "Downloading latest version of Cloudinit and Qemu Patches..." >> $log_file

    wget --no-check-certificate https://raw.githubusercontent.com/Pinous-Heberg/proxmox-win-cloudinit/main/proxmox-patch/Cloudinit.pm.patch -O /tmp/Cloudinit.pm.patch 2>/dev/null
    wget --no-check-certificate https://raw.githubusercontent.com/Pinous-Heberg/proxmox-win-cloudinit/main/proxmox-patch/Qemu.pm.patch -O /tmp/Qemu.pm.patch 2>/dev/null
}

function check_patch_compatibility() {
    cloudcheck=$(patch --force --forward --backup -p0 --directory / --input "/tmp/Cloudinit.pm.patch" --dry-run && echo "You can apply patch" || { echo "Can't apply patch!";})
    qemucheck=$(patch --force --forward --backup -p0 --directory / --input "/tmp/Qemu.pm.patch" --dry-run && echo "You can apply patch" || { echo "Can't apply patch!";})
    if [ "$cloudcheck" == "You can apply patch" ] && [ "$qemucheck" == "You can apply patch" ]; then
         echo 0
    else
        echo 1
    fi
}

function backup_original_files() {
    if [ ! -d $backup_path ]; then
        mkdir -p $backup_path
    fi

    if [ ! -f $qemu_path ] || [ ! -f $cloudinit_path ] || [ ! -f $qemu_path ] && [ ! -f $cloudinit_path ]; then
        echo "Original files not found. Exiting..." >> $log_file
        exit 1
    fi

    echo "Backing up original files..." >> $log_file

    if [ -f $backup_path/Cloudinit.pm ] || [ -f $backup_path/Qemu.pm ] || [  -f $backup_path/Cloudinit.pm] && [ -f $backup_path/Qemu.pm ]; then
        rm -rf $backup_path/Cloudinit.pm
        rm -rf $backup_path/Qemu.pm
    fi
    cp $qemu_path $backup_path
    cp $cloudinit_path $backup_path

    echo "Original files backed up to $backup_path" >> $log_file
}

function apply_patch() {
    echo "Applying patch..." >> $log_file
    patch --force --forward --backup -p0 --directory / --input "/tmp/Cloudinit.pm.patch"
    patch --force --forward --backup -p0 --directory / --input "/tmp/Qemu.pm.patch"
    echo "Patch applied successfully !" >> $log_file
}

function restartproxy() {
    echo "Restarting Proxmox VE Proxy..." >> $log_file
    service pveproxy restart
    if [ $? -eq 0 ]; then
        echo "Proxmox VE Proxy restarted successfully !" >> $log_file
    else
        echo "Proxmox VE Proxy restart failed ! Restoring original files..." >> $log_file
        restore_original_files
    fi
}

function restore_original_files() {
    echo "Restoring original files..." >> $log_file
    cp $backup_path/Cloudinit.pm $cloudinit_path
    cp $backup_path/Qemu.pm $qemu_path
    echo "Original files restored successfully !" >> $log_file
    restartproxy
}
main()
