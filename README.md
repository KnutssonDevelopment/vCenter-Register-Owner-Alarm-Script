# Register Owner or Creator of a Virtual Machine upon creation in VMware vSphere
This is a script for setting the owner and creation date of a Virtual Machine upon creation or deployment

The script is meant to be run by an alarm set in vCenter.

The script can be placed almost anywhere on your vCenter Appliance, but I recommend placing it in "/opt/scripts/alarmscripts"

## Notes
When deploying a VM from an OVF, there user deploying the VM is an estimation. There is not solid link between the OVF Import task done by the user, and the VM Deplyoment task done by the vpxd service.

## Prerequisites
You need to create a user that has access to set custom attributes vCenter tree. Normally set in the top of the tree (On the vCenter object) You should create a custom role for this limit the users permissions as much as possible in case the account gets compromised.

## Install
### Overview
- Create a Role in vCenter
- Create a User or use existing user
- Give the user access to set custom attributes by using the new role
- Copy the script to vCenter
- Change the username and password variables in the script to suit your needs or enable password obfuscation and run the script from the console to create the secrets file
- Set the correct file rights on the file to prohibit non root users from reading the service account password
- Create the custom attribute in vCenter. The script can do it automatically, but the default role does not have access
- Create the trigger alarm
- Test by Creating a new vm
- Test by Deploying a new vm from a template or ovf
- Test by Cloning a vm

### Install Instructions
First make sure all prerequisites are in place. Check the Overview.

**Copy the script to vCenter**
I recommend placing the scripts in the following location the location: /opt/scripts/alarmscripts
The above location will be assumed during the following steps.
```
mkdir -p /opt/scripts/alarmscripts
cd /opt/scripts/alarmscripts
wget https://github.com/KnutssonDevelopment/vCenter-Register-Owner-Alarm-Script/blob/main/retrieve_information.py
wget https://github.com/KnutssonDevelopment/vCenter-Register-Owner-Alarm-Script/blob/main/vm.alarm.new-vm.py
chmod 700 /opt/scripts/alarmscripts/vm.alarm.new-vm.py
chmod 700 /opt/scripts/alarmscripts/retrieve_information.py

#This should only be done for version 8.x as the vpxd service now runs as a non root user
chown vpxd:root /opt/scripts/alarmscripts/vm.alarm.new-vm.py
chown vpxd:root /opt/scripts/alarmscripts/retrieve_information.py
```
**The rest is relevant for all versions**
Edit the script and set either:
1) the username and password variable to the service account you made in vCenter and the ENABLE_PASSWORD_OBFUSCATION = False
or
2) Do not set the username and password varables, but make sure the ENABLE_PASSWORD_OBFUSCATION = True

If you set the ENABLE_PASSWORD_OBFUSCATION = True, you need to run the script the set the credentials.
```
cd /opt/scripts/alarmscripts
./vm.alarm.new-vm.py
```
Now set the credentials in the file: /opt/scripts/alarmscripts/secrets.txt and run the script again.
```
cd /opt/scripts/alarmscripts
vi secrets.py

./vm.alarm.new-vm.py

# Set the permission for the secrets file (Only for vCenter 8.x)
chown vpxd:root /opt/scripts/alarmscripts/secrets.txt
```

You should have the following files in /opt/scripts/alarmscripts:
- vm.alarm.new-vm.py
- retrieve_information.py
- secrets.txt (Only if you set ENABLE_PASSWORD_OBFUSCATION = True)

No you can go ahead and create and test the alarms.

### vCenter Role - Example
|Role Name|Rule Privileges|
|---------------------|------------------------------|
|Set Custom Attributes|Global -> Set custom attribute|

### vCenter User - Example
|Username|Permission Path|Role|Propagate to children|
|------------------------|--------------|---------------------|---|
|alarm_user@vsphere.local|vCenter Object|Set Custom Attributes|YES|

### Alarm Comfigurations
|Setting|Value|
|-------------------------------|--------------------------------------------------|
|Alarm Name|Add Creator Information to Virtual Machine on Creation|
|Target Type|Virtual Machines|
|Alarm 1 - Rule Trigger|Creating VM|
|Alarm 1 - Trigger the alarm and|Keep the target's current starte|
|Alarm 1 - Run Script|Enabled|
|Alarm 1 - Run this Script|/opt/scripts/alarmscripts/vm.alarm.new-vm.py|
|Alarm 2 - Rule Trigger|Deploying VM|
|Alarm 2 - Trigger the alarm and|Keep the target's current starte|
|Alarm 2 - Run Script|Enabled|
|Alarm 2 - Run this Script|/opt/scripts/alarmscripts/vm.alarm.new-vm.py|
|Alarm 3 - Rule Trigger|VM cloned|
|Alarm 3 - Trigger the alarm and|Keep the target's current starte|
|Alarm 3 - Run Script|Enabled|
|Alarm 3 - Run this Script|/opt/scripts/alarmscripts/vm.alarm.new-vm.py|

### Troubleshooting
The custom attribute is not set, or does not exists on the VM. You need to manually create the custom attribute in vCenter.

## Credits
I did take inspiration from Bryan McClellan and MARK III SYSTEMS BLOG.

I just didn't like the python code, and I wanted to improve it a little. If you need inspiration building the alarms have a look at Mark's blog.

### Links
- https://gist.github.com/mccbryan3/c628930075407f2467eba88326001871
- https://www.markiiisys.com/blog/vm-alarm-script/


