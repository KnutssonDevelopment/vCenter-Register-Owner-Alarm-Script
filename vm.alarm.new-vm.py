#!/bin/python3
import pytz
from datetime import datetime
import ssl
import os
import sys
import socket
from pathlib import Path

local_tz = pytz.timezone('Europe/Copenhagen')
now = datetime.now(local_tz)

creatorCustomAttribute = 'CreatedBy'

sys.path.extend(os.environ['VMWARE_PYTHON_PATH'].split(';'))
script_path=Path(os.path.abspath(__file__)).parent
sys.path.append(script_path)

import retrieve_information
from pyVim import connect
from pyVim.connect import SmartConnect
from pyVmomi import vim


def get_vcenter_connection(hostname=None):

    s=ssl.SSLContext(ssl.PROTOCOL_SSLv23) # For VC 6.5/6.0 s=ssl.SSLContext(ssl.PROTOCOL_TLSv1)
    s.verify_mode=ssl.CERT_NONE

    try:
        u, p = retrieve_information.manage_secrets()
        si = SmartConnect(host=hostname, user=u, pwd=p, sslContext=s)
        return si
    except Exception as e:
        print(e)
        return None


def find_vm_by_id(content, vmid, name):
    vmtype = [vim.VirtualMachine]
    container = content.viewManager.CreateContainerView(content.rootFolder, vmtype, True)
    for entry in container.view:
        if vmid and vmid in str(entry) and name == entry.name:
            return entry
    return None


# Check if custom attribute already exists
def custom_attribute_exists(content, field_name):
    for field in content.customFieldsManager.field:
        if field.name == field_name:
            return True
    return False


# Create a new custom attribute
def create_custom_attribute(content, field_name, mo_type=vim.VirtualMachine):
    if not custom_attribute_exists(content, field_name):
        content.customFieldsManager.AddCustomFieldDef(name=field_name, moType=mo_type)


def main():
    alarm_target_name = os.getenv('VMWARE_ALARM_TARGET_NAME', None)
    alarm_target_id = os.getenv('VMWARE_ALARM_TARGET_ID', None)
    alarm_user = os.getenv('VMWARE_ALARM_EVENT_USERNAME', None)
    alarm_vm = os.getenv('VMWARE_ALARM_EVENT_VM', None)

    if (not alarm_vm):
        print("ERROR(1): Variables not set")
        exit(1)

    hostname = socket.gethostname()

    vc_connection = get_vcenter_connection(hostname)
    if (not vc_connection):
        print("ERROR(2): Could not connect to vCenter: {hostname}")
        exit(2)

    content=vc_connection.content

    vm = find_vm_by_id(content, alarm_target_id, alarm_target_name)

    if (not vm):
        print(f"ERROR(3): Could not find vm with name: {alarm_target_name}")
        exit(3)

    try:
        create_custom_attribute(content, creatorCustomAttribute)

    except vim.fault.NoPermission:
        print(f"ERROR(4): Missing permissions to create custom attribute: '{creatorCustomAttribute}'.")
        exit(4)

    try:
        vm.setCustomValue(creatorCustomAttribute, f"{alarm_user} - {str(now.strftime('%Y-%m-%d %H:%M:%S %Z%z'))}")
    except Exception as e:
        print("ERROR(4): Could not set custom attributes")
        print(e)
        exit(4)

if __name__ == "__main__":
    main()
