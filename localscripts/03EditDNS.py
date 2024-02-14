import subprocess
import sys
import wmi

def get_disk_letter_from_name(disk_name):
    c = wmi.WMI()
    for disk in c.Win32_LogicalDisk():
        if disk.VolumeName == disk_name:
            return disk.DeviceID[:-1]
    return None

def get_dns_from_file(file_path):
    with open(file_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            if 'dns_nameservers' in line:
                dns_line = line.strip().split(' ')
                dns_servers = dns_line[1:]
                if len(dns_servers) > 2:
                    dns_servers = dns_servers[:2]
                return dns_servers
    return None

def set_dns(dns_servers):
    if dns_servers is not None:
        ps_command = "Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses '{}' -PassThru".format("', '".join(dns_servers))
        subprocess.call(["powershell.exe", ps_command])
        print("DNS set to:", dns_servers)
    else:
        print("No DNS servers found.")

disk_name = "config-2"
disk_letter = get_disk_letter_from_name(disk_name)
if disk_letter is None:
    print("Disk not found:", disk_name)
    sys.exit(1)

file_path = r"{}:\OPENSTACK\CONTENT\0000".format(disk_letter)
dns_servers = get_dns_from_file(file_path)
set_dns(dns_servers)
sys.exit(0)
