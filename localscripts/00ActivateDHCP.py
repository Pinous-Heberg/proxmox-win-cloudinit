import os
import json
import sys
import wmi
from cloudbaseinit.osutils import factory as osutils_factory

def load_json_variable(file_path, variable):
    file = open(file_path)
    data = json.load(file)
    file.close()
    return data.get(variable)

def find_drive(file_path):
    for number in range(65, 91):
        drive_letter = chr(number)
        if os.path.exists(drive_letter + file_path):
            return drive_letter + file_path
    print("\nSearched file could not be found on any drive with path: " + file_path)
    return False

def get_name_by_mac(mac):
    osutils = osutils_factory.get_os_utils()
    name = osutils.get_network_adapter_name_by_mac_address(mac)
    return name

def activate_dhcp(name, family):
    osutils = osutils_factory.get_os_utils()
    osutils._fix_network_adapter_dhcp(name, True, family)

# Variables
meta_data_path = find_drive(":\OPENSTACK\LATEST\META_DATA.json")
# 2 for IPv4 and 6 for IPv6
family = 2

# Execute
if meta_data_path != False:
    macs = load_json_variable(meta_data_path, "dhcp")

    if macs is not None:
        for mac in macs:
            name = get_name_by_mac(mac)
            activate_dhcp(name, family)

    sys.exit(1001)
else:
    sys.exit(0)
