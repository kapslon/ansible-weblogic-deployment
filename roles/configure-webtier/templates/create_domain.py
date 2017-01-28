
mwHome='{{ ohs_oracle_home }}'
domainHome='{{ ohs_domain_home }}'
readTemplate(mwHome +'/wlserver/common/templates/wls/base_standalone.jar')
addTemplate(mwHome +'/ohs/common/templates/wls/ohs_standalone_template.jar')
domainName='Ohs'
nodeManagerUsername='weblogic'
nodeManagerPassword='{{ weblogic_admin_pass }}'
nodemanagerHome='{{ nm_home }}'
nodeManagerHost='{{ inventory_hostname }}'
nodeManagerPort='{{ nodemanager_ohs_port }}'
nodeManagerMode='SSL'
jdkHome='{{ java_home }}'


cd('/')
create(domainName, 'SecurityConfiguration') 
cd('SecurityConfiguration/' + domainName)
set('NodeManagerUsername',nodeManagerUsername)
set('NodeManagerPasswordEncrypted',nodeManagerPassword)
setOption('JavaHome', jdkHome )

cd('/Machines/localmachine/NodeManager/localmachine')
cmo.setListenAddress(nodeManagerHost);
cmo.setListenPort(int(nodeManagerPort));
cmo.setNMType(nodeManagerMode);

writeDomain(domainHome)
