import subprocess
import os
import wmi

def get_disk_letter_from_name(disk_name):
    c = wmi.WMI()
    for disk in c.Win32_LogicalDisk():
        if disk.VolumeName == disk_name:
            return disk.DeviceID[:-1]
    return None

disk_name = "config-2"
disk_letter = get_disk_letter_from_name(disk_name)
if disk_letter is None:
    print("Disk not found:", disk_name)
    sys.exit(1)

user_data_file =  r"{}:\OPENSTACK\LATEST\USER_DATA".format(disk_letter)

def check_user_data_upgrade():
    with open(user_data_file, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if line.strip() == "package_upgrade: true":
                return True
    return False

def perform_system_upgrade():
    print("Performing system upgrade...")
    subprocess.call(["powershell.exe", "Install-WindowsUpdate -AcceptAll -AutoReboot"])
    print("System upgrade completed.")

if check_user_data_upgrade():
    perform_system_upgrade()
else:
    print("No package upgrade directive found in USER_DATA.")
