#!/bin/python3
import pytz
from datetime import datetime
import ssl
import os
import sys

username = "alarm_user@vsphere.local"
password = "PASSWORD"

local_tz = pytz.timezone('Europe/Copenhagen')
now = datetime.now(local_tz)

sys.path.extend(os.environ['VMWARE_PYTHON_PATH'].split(';'))

from pyVim import connect
from pyVim.connect import SmartConnect
from pyVmomi import vim


def get_vcenter_connection(user, pwd):
    import socket

    hostname = socket.gethostname()

    s=ssl.SSLContext(ssl.PROTOCOL_SSLv23) # For VC 6.5/6.0 s=ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode=ssl.CERT_NONE

    try:
        si = SmartConnect(host=hostname, user=user, pwd=pwd, sslContext=s)
        return si
    except:
        return None


def find_vm_by_id(content, vmid, name):
    vmtype = [vim.VirtualMachine]
    container = content.viewManager.CreateContainerView(content.rootFolder, vmtype, True)
    for entry in container.view:
        if vmid and vmid in str(entry) and name == entry.name:
            return entry
    return None


def main():
    alarm_target_name = os.getenv('VMWARE_ALARM_TARGET_NAME', None)
    alarm_target_id = os.getenv('VMWARE_ALARM_TARGET_ID', None)
    alarm_user = os.getenv('VMWARE_ALARM_EVENT_USERNAME', None)
    alarm_vm = os.getenv('VMWARE_ALARM_EVENT_VM', None)

    if (not alarm_vm):
        print("ERROR(1): Variables not set")
        exit(1)

    vc_connection = get_vcenter_connection(username, password)
    if (not vc_connection):
        print("ERROR(2): Could not connect to vCenter")
        exit(2)

    content=vc_connection.content

    vm = find_vm_by_id(content, alarm_target_id, alarm_target_name)

    if (not vm):
        print(f"ERROR(3): Could not find vm with name: {alarm_target_name}")
        exit(3)

    try:
        vm.setCustomValue('vm.owner', alarm_user)
        vm.setCustomValue('vm.provisioned', str(now.strftime('%Y-%m-%d %H:%M:%S %Z%z')))
    except Exception as e:
        print("ERROR(4): Could not set custom attributes")
        print(e)
        exit(4)

if __name__ == "__main__":
    main()
