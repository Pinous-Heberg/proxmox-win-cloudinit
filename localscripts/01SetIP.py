import subprocess
import sys
import wmi

def get_disk_letter_from_name(disk_name):
    c = wmi.WMI()
    for disk in c.Win32_LogicalDisk():
        if disk.VolumeName == disk_name:
            return disk.DeviceID[:-1]
    return None

def get_set_ipv6_and_gateway_from_network_config():
    ps_command = "Get-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv6"
    output = subprocess.check_output(["powershell.exe", ps_command])
    lines = output.decode('utf-8').split('\r\n')
    ipv6_addresses = []
    gateway = None
    for line in lines:
        if 'Address' in line:
            parts = line.split()
            for part in parts:
                if ':' in part and part.count(':') > 1:
                    ipv6_addresses.append(part.split('/')[0])
        if 'Preferred' in line:
            parts = line.split()
            for i in range(len(parts)):
                if parts[i] == 'Preferred':
                    if i+1 < len(parts) and ':' in parts[i+1] and parts[i+1].count(':') > 1:
                        gateway = parts[i+1] if i+1 < len(parts) else None
    return ipv6_addresses, gateway

def get_ipv6_and_gateway_from_file(file_path):
    ipv6_addresses = []
    gateway = None
    with open(file_path, 'r') as file:
        for line in file:
            if 'address' in line:
                parts = line.split()
                for part in parts:
                    if ':' in part and part.count(':') > 1:
                        ipv6_addresses.append(part.split('/')[0])
            if 'gateway' in line:
                parts = line.split()
                for i in range(len(parts)):
                    if parts[i] == 'gateway':
                        gateway = parts[i+1] if i+1 < len(parts) else None
    return ipv6_addresses, gateway

def set_ipv6(ipv6_addresses, gateway):
    if ipv6_addresses != get_set_ipv6_and_gateway_from_network_config()[0]:
        ps_command = "Remove-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv6 -Confirm:$false"
        subprocess.call(["powershell.exe", ps_command])
        print("IPv6 addresses removed from network config.")
        
        ps_command = "New-NetIPAddress -InterfaceAlias 'Ethernet' -IPAddress {} -PrefixLength 64".format(','.join(ipv6_addresses))
        subprocess.call(["powershell.exe", ps_command])
        
        ps_command_gateway = "New-NetRoute -InterfaceAlias 'Ethernet' -DestinationPrefix ::/0 -NextHop {}".format(gateway)
        subprocess.call(["powershell.exe", ps_command_gateway])
        print("IPv6 addresses and gateway set successfully.")
    else:
        print("IPv6 addresses and gateway already set in network config.")
    
def get_set_ipv4_and_gateway_from_network_config():
    ps_command = "Get-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv4"
    output = subprocess.check_output(["powershell.exe", ps_command])
    lines = output.decode('utf-8').split('\r\n')
    ipv4_addresses = []
    gateway = None
    for line in lines:
        if 'Address' in line:
            parts = line.split()
            for part in parts:
                if '.' in part and part.count('.') == 3:
                    ipv4_addresses.append(part)
        if 'Preferred' in line:
            parts = line.split()
            for i in range(len(parts)):
                if parts[i] == 'Preferred':
                    if i+1 < len(parts) and '.' in parts[i+1] and parts[i+1].count('.') == 3:
                        gateway = parts[i+1] if i+1 < len(parts) else None
    return ipv4_addresses, gateway

def get_ipv4_and_gateway_from_file(file_path):
    ipv4_addresses = []
    gateway = None
    with open(file_path, 'r') as file:
        for line in file:
            if 'address' in line:
                parts = line.split()
                for part in parts:
                    if '.' in part and part.count('.') == 3:
                        ipv4_addresses.append(part)
            if 'gateway' in line:
                parts = line.split()
                for i in range(len(parts)):
                    if parts[i] == 'gateway':
                        if i+1 < len(parts) and '.' in parts[i+1] and parts[i+1].count('.') == 3:
                            gateway = parts[i+1] if i+1 < len(parts) else None
    return ipv4_addresses, gateway

def set_ipv4(ipv4_addresses, gateway):
    if ipv4_addresses != get_set_ipv4_and_gateway_from_network_config()[0]:
        ps_command = "Remove-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -Confirm:$false"
        subprocess.call(["powershell.exe", ps_command])
        print("IPv4 addresses removed from network config.")
        
        ps_command = "New-NetIPAddress -InterfaceAlias 'Ethernet' -IPAddress {} -PrefixLength 24".format(','.join(ipv4_addresses))
        subprocess.call(["powershell.exe", ps_command])
        
        ps_command_gateway = "New-NetRoute -InterfaceAlias 'Ethernet' -DestinationPrefix 0.0.0.0/0 -NextHop {}".format(gateway)
        subprocess.call(["powershell.exe", ps_command_gateway])
        print("IPv4 addresses and gateway set successfully.")
    else:
        print("IPv4 addresses and gateway already set in network config.")

disk_name = "config-2"
disk_letter = get_disk_letter_from_name(disk_name)
if disk_letter is None:
    print("Disk not found:", disk_name)
    sys.exit(1)

file_path = r"{}:\OPENSTACK\CONTENT\0000".format(disk_letter)
ipv4_addresses, gateway = get_ipv4_and_gateway_from_file(file_path)
set_ipv4(ipv4_addresses, gateway)

ipv6_addresses, gateway = get_ipv6_and_gateway_from_file(file_path)
set_ipv6(ipv6_addresses, gateway)

sys.exit(0)
