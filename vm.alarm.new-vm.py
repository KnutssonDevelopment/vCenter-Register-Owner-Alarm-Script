#!/bin/python3
import ssl
import os
import sys
import socket

from pathlib import Path
import pytz
from datetime import datetime, timedelta

sys.path.extend(os.environ['VMWARE_PYTHON_PATH'].split(';'))
script_path=Path(os.path.abspath(__file__)).parent
sys.path.append(script_path)

from pyVim import connect
from pyVim.connect import SmartConnect
from pyVmomi import vim

local_tz = pytz.timezone('Europe/Copenhagen')
now = datetime.now(local_tz)
task_msg = "Task: Import OVF package"

# Custom Variables
creatorCustomAttribute = 'CreatedBy'
ENABLE_PASSWORD_OBFUSCATION = True

if (ENABLE_PASSWORD_OBFUSCATION):
    import retrieve_information
    username, password = retrieve_information.manage_secrets()
else:
    username = "alarm_user@vsphere.local"
    password = "PASSWORD"

def get_vcenter_connection(hostname=None, username=None, password=None):
    s=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    s.check_hostname = False
    s.verify_mode=ssl.CERT_NONE

    try:
        si = SmartConnect(host=hostname, user=username, pwd=password, sslContext=s)
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


def get_vm_events(si: vim.ServiceInstance, vm: vim.VirtualMachine, max_events=1000):
    by_entity = vim.event.EventFilterSpec.ByEntity(entity=vm, recursion="self")
    filter_spec = vim.event.EventFilterSpec(entity=by_entity, maxCount=max_events)

    content=si.content
    event_manager = content.eventManager
    events = event_manager.QueryEvent(filter_spec)

    return events


def get_all_task_events_by_compute_resource(si: vim.ServiceInstance, start: datetime, end: datetime, compute_resource):
    events_by_time = vim.event.EventFilterSpec.ByTime(beginTime=start, endTime=end)
    events_by_entity = vim.event.EventFilterSpec.ByEntity(entity=compute_resource.computeResource, recursion='self')
    filter_spec = vim.event.EventFilterSpec(time=events_by_time, entity=events_by_entity, eventTypeId=['vim.event.TaskEvent'])
    content=si.content
    event_manager = content.eventManager
    events = event_manager.QueryEvent(filter_spec)

    return events


# Create a new custom attribute
def create_custom_attribute(content, field_name, mo_type=vim.VirtualMachine):
    if not custom_attribute_exists(content, field_name):
        content.customFieldsManager.AddCustomFieldDef(name=field_name, moType=mo_type)


def main():
    alarm_target_name = os.getenv('VMWARE_ALARM_TARGET_NAME', None)
    alarm_target_id = os.getenv('VMWARE_ALARM_TARGET_ID', None)
    alarm_user = os.getenv('VMWARE_ALARM_EVENT_USERNAME', None)

    if (not alarm_target_name):
        print("ERROR(1): Variables not set")
        print("If you want to run manually you need to set the following environment variables:")
        print("Example Commands:")
        print("-----------------------------------------------------")
        print('export VMWARE_ALARM_TARGET_NAME="TestVM"')
        print('export VMWARE_ALARM_TARGET_ID="vm-123456"')
        print('export VMWARE_ALARM_EVENT_USERNAME="DOMAIN\\User"')
        
        exit(1)

    hostname = socket.gethostname()

    # Connecting to vCenter
    vc_connection = get_vcenter_connection(hostname, username, password)
    if (not vc_connection):
        print(f"ERROR(2): Could not connect to vCenter: {hostname}")
        exit(2)

    # Getting VirtualMachine
    content=vc_connection.content
    vm = find_vm_by_id(content, alarm_target_id, alarm_target_name)

    if (not vm):
        print(f"ERROR(3): Could not find vm with name: '{alarm_target_name}' and id: '{alarm_target_id}'")
        exit(3)


    if "vpxd-extension" in alarm_user:
        # Trying to get the right user account from the events on the VirtualMachine
        events = get_vm_events(si=vc_connection, vm=vm, max_events=1)

        if len(events) == 0:
            print(f"WARNING(1): Did not find any event for VirtualMachine: {alarm_target_name}")
            alarm_user = "USER Unknown"
        else:
            # Get the first event ever created on this VM
            vm_created_time = events[0].createdTime
            compute_resource  = events[0].computeResource

            possible_events = []
            search_interval = 1
            overlap_interval = 1
            while len(possible_events) == 0:
                start = vm_created_time - timedelta(minutes=search_interval)
                end = vm_created_time - timedelta(minutes=(search_interval - overlap_interval))
                global_events = get_all_task_events_by_compute_resource(si=vc_connection, start=start, end=end, compute_resource=compute_resource)

                for event in global_events:
                    if event.fullFormattedMessage == task_msg:
                        if event.computeResource.computeResource == compute_resource.computeResource:
                            print(f"{event.createdTime} {event.userName} {event.fullFormattedMessage}")
                            possible_events.append(event)

                if len(possible_events) > 0:
                    # We found an event
                    break
                elif search_interval > 240:
                    # We were unable to find the event within 4 hours of the deployment
                    break
                else:
                    # Keep looking
                    search_interval += 1

            if len(possible_events) > 0:
                alarm_user = possible_events[0].userName
            else:
                alarm_user = "USER Unknown"

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
