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
    ipv6_addresses = []
    gateway = None
    ps_command = "Get-NetIPAddress -InterfaceAlias 'Ethernet'"
    try:
        output = subprocess.check_output(["powershell.exe", ps_command])
        # evite que le powershell ne fasse une erreur si il n'y a pas d'adresse IPv6
        if 'Address' not in output.decode('utf-8'):
            return ipv6_addresses, gateway
    except subprocess.CalledProcessError as e:
        print(f"Error executing PowerShell command: {e}")
        return ipv6_addresses, gateway
    lines = output.decode('utf-8').split('\r\n')

    for line in lines:
        if 'SELECT * FROM MSFT_NetIPAddress  WHERE ((InterfaceAlias LIKE \'Ethernet\')) AND ((AddressFamily = 23))' in line:
            return ipv6_addresses, gateway
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
        if 'PrefixOrigin' in line:
            if 'RouterAdvertisement' in line:
                print("IPv6 addresses and gateway is not set.")
                gateway = None
                ipv6_addresses = None
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
    if ipv6_addresses:
        if ipv6_addresses != get_set_ipv6_and_gateway_from_network_config()[0]:
            ps_command = "Remove-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv6 -Confirm:$false"
            subprocess.call(["powershell.exe", ps_command])
            ps_command_remove = "Remove-NetRoute -InterfaceAlias 'Ethernet' -AddressFamily IPv6 -Confirm:$false"
            subprocess.call(["powershell.exe", ps_command_remove])
            print("IPv6 addresses removed from network config.")
            ps_command = "New-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv6 -IPAddress {} -PrefixLength 64".format(','.join(ipv6_addresses))
            subprocess.call(["powershell.exe", ps_command])
            ps_command_gateway = "New-NetRoute -InterfaceAlias 'Ethernet' -AddressFamily IPv6 -DestinationPrefix ::/0 -NextHop {}".format(gateway)
            subprocess.call(["powershell.exe", ps_command_gateway])
            print("IPv6 addresses and gateway set successfully.")
        else:
            print("IPv6 addresses and gateway already set in network config.")
    else:
        print("No IPv6 detected")
        
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
    if ipv4_addresses:
        if ipv4_addresses != get_set_ipv4_and_gateway_from_network_config()[0]:
            ps_command = "Remove-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -Confirm:$false"
            subprocess.call(["powershell.exe", ps_command])
            ps_command_remove = "Remove-NetRoute -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -Confirm:$false"
            subprocess.call(["powershell.exe", ps_command_remove])
            print("IPv4 addresses removed from network config.")
            
            ps_command = "New-NetIPAddress -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -IPAddress {} -PrefixLength 24".format(','.join(ipv4_addresses))
            subprocess.call(["powershell.exe", ps_command])

            ps_command_gateway = "New-NetRoute -InterfaceAlias 'Ethernet' -AddressFamily IPv4 -DestinationPrefix 0.0.0.0/0 -NextHop {}".format(gateway)
            subprocess.call(["powershell.exe", ps_command_gateway])

            print("IPv4 addresses and gateway set successfully.")
        else:
            print("IPv4 addresses and gateway already set in network config.")
    else:
        print("No IPv4 detected")

def set_dns():
    ps_command = "Get-DnsClientServerAddress -InterfaceAlias 'Ethernet'"
    output = subprocess.check_output(["powershell.exe", ps_command])
    if b'1.1.1.1' in output and b'2606:4700:4700::1111' in output and b'1.0.0.1' in output and b'2606:4700:4700::1001' in output:
        print("DNS already set")
        return
    ps_command_ipv4 = "Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses '1.1.1.1', '1.0.0.1' -PassThru"
    subprocess.call(["powershell.exe", ps_command_ipv4])
    print("IPv4 DNS set to: 1.1.1.1, 1.0.0.1")
    ps_command_ipv6 = "Set-DnsClientServerAddress -InterfaceAlias 'Ethernet' -ServerAddresses '2606:4700:4700::1111', '2606:4700:4700::1001' -PassThru"
    subprocess.call(["powershell.exe", ps_command_ipv6])
    print("IPv6 DNS set to:", ['2606:4700:4700::1111', '2606:4700:4700::1001'])

disk_name = "config-2"
disk_letter = get_disk_letter_from_name(disk_name)
if disk_letter is None:
    print("Disk not found:", disk_name)
    sys.exit(1)

file_path = r"{}:\OPENSTACK\CONTENT\0000".format(disk_letter)
ipv4_addresses, gateway = get_ipv4_and_gateway_from_file(file_path)
set_ipv4(ipv4_addresses, gateway)
ipv6_addresses, gateway6 = get_ipv6_and_gateway_from_file(file_path)
set_ipv6(ipv6_addresses, gateway6)
set_dns()

sys.exit(0)
