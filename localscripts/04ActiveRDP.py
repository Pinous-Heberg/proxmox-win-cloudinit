import subprocess

subprocess.run(["reg", "add", "HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Control\Terminal Server", "/v", "fDenyTSConnections", "/t", "REG_DWORD", "/d", "0", "/f"])

subprocess.run(["netsh", "advfirewall", "firewall", "set", "rule", "group=\"Remote Desktop\"", "new", "enable=yes"])
