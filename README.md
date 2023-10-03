# Register Owner or Creator of a Virtual Machine upon creation in VMware vSphere

This is a script for setting the owner and creation date of a Virtual Machine upon creation or deployment

The script is meant to be run by an alarm set in vCenter.

The script can be placed almost anywhere on your vCenter Appliance, but I recommend placing it in "/root/alarmscripts"

## Prerequisites
You need to create a user that has access to set custom attributes vCenter tree. Normally set in the top of the tree (On the vCenter object) You should create a custom role for this limit the users permissions as much as possible in case the account gets compromised.

## TODO
- Create a Role in vCenter
- Create a User or use existing user
- Give the user access to set custom attributes by using the new role
- Copy the script to vCenter
- Set the correct file rights on the file to prohibit non root users from reading the service account password
- Create the trigger alarm
- Test by Creating a new vm
- Test by Deploying a new vm from a template or ovf

### vCenter Role - Example
|Role Name|Rule Privileges|
|---------------------|------------------------------|
|Set Custom Attributes|Global -> Set custom attribute|

### vCenter User - Example
|Username|Permission Path|Role|Propagate to children|
|------------------------|--------------|---------------------|---|
|alarm_user@vsphere.local|vCenter Object|Set Custom Attributes|YES|

## Credits
I did take inspiration from Bryan McClellan and MARK III SYSTEMS BLOG.

I just didn't like the python code, and I wanted to improve it a little. If you need inspiration building the alarms have a look at Mark's blog.

### Links
- https://gist.github.com/mccbryan3/c628930075407f2467eba88326001871
- https://www.markiiisys.com/blog/vm-alarm-script/


