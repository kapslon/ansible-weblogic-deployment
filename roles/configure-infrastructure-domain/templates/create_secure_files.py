nmConnect('weblogic','{{ weblogic_admin_pass }}', '{{ inventory_hostname }}','{{ nodemanager_port }}','{{ domain_name }}')
storeUserConfig(userConfigFile='{{ wlscripts }}/secure/configfile.secure', userKeyFile='{{ wlscripts }}/secure/keyfile.secure',nm='true');
exit

