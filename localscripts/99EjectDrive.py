import os
import subprocess
import sys

def remove_drive():
    drive_letter = os.popen('wmic logicaldisk where VolumeName="config-2" get Caption | findstr /I ":"').read()
    ps_command = "powershell \"(new-object -COM Shell.Application).NameSpace(17).ParseName(\'" + drive_letter.strip() + "\').InvokeVerb(\'Eject\')\""
    if drive_letter:
        subprocess.call(["powershell.exe", ps_command])
        print("Drive " + drive_letter.strip() + " ejected")
        
remove_drive()
sys.exit(0)
