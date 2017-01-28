WLHOME      = '{{ domains_location }}'
DOMAIN      = '{{ domain_name }}'
DOMAIN_PATH = '{{ aserver_home }}'
APP_PATH    = '{{ application_home }}'

HOSTS = {{ ansible_play_hosts }}
ADMIN_PASSWORD = '{{ weblogic_admin_pass }}'
ADMIN_SERVER   = 'AdminServer'
ADMIN_USER     = 'weblogic'

SERVER_ADDRESS = HOSTS[0]

OSB_SERVER_PORT = {{ osb_server_port }}

JAVA_HOME      = '{{ java_home }}'

db_server_name = '{{ dbserver_name }}'
db_server_port = '{{ dbserver_port }}'
db_service = '{{ dbserver_service }}'

JSSE_ENABLED     = false
DEVELOPMENT_MODE = false
WEBTIER_ENABLED  = false

SOA_REPOS_DBURL          = 'jdbc:oracle:thin:@//' + db_server_name + ':' + db_server_port + '/' + db_service
SOA_REPOS_DBUSER_PREFIX  = '{{ repository_prefix }}'
SOA_REPOS_DBPASSWORD     = '{{ datasource_password }}'


def changeDatasourceToXA(datasource):
  print 'Change datasource '+datasource
  cd('/')
  cd('/JDBCSystemResource/'+datasource+'/JdbcResource/'+datasource+'/JDBCDriverParams/NO_NAME_0')
  set('DriverName','oracle.jdbc.xa.client.OracleXADataSource')
  set('UseXADataSourceInterface','True') 
  cd('/JDBCSystemResource/'+datasource+'/JdbcResource/'+datasource+'/JDBCDataSourceParams/NO_NAME_0')
  set('GlobalTransactionsProtocol','TwoPhaseCommit')
  cd('/')

def changeManagedServer(server,port,machine):
  cd('/Servers/'+server)
  set('Machine'      ,machine)
  set('ListenAddress',machine)
  set('ListenPort'   ,port)

  create(server,'ServerStart')
  cd('ServerStart/'+server)
  set('JavaVendor','Sun')
  set('JavaHome'  , JAVA_HOME)

  cd('/Server/'+server)
  create(server,'SSL')
  cd('SSL/'+server)
  set('Enabled'                    , 'False')
  set('HostNameVerificationIgnored', 'True')

  if JSSE_ENABLED == true:
    set('JSSEEnabled','True')
  else:
    set('JSSEEnabled','False')  

  cd('/Server/'+server)
  create(server,'Log')
  cd('/Server/'+server+'/Log/'+server)
  set('FileCount'    , 10)
  set('FileMinSize'  , 5000)
  set('RotationType' ,'byTime')
  set('FileTimeSpan' , 24)


readDomain(DOMAIN_PATH)

cd('/')


print 'Adding Templates'
#print 'Adding OSB Template'
#addTemplate('{{ oracle_home }}/osb/common/templates/wls/oracle.osb.common_template.jar')
print('Extend...API Manager')
addTemplate('{{ oracle_home }}/osb/common/templates/wls/oracle.apimanager_template.jar')

dumpStack()


print 'Set datasource LocalScvTblDataSource'
cd('/JDBCSystemResource/LocalSvcTblDataSource/JdbcResource/LocalSvcTblDataSource/JDBCDriverParams/NO_NAME_0')
set('URL',SOA_REPOS_DBURL)
set('PasswordEncrypted',SOA_REPOS_DBPASSWORD)
cd('Properties/NO_NAME_0/Property/user')
set('Value',SOA_REPOS_DBUSER_PREFIX+'_STB')

print 'Call getDatabaseDefaults which reads the service table'
getDatabaseDefaults()    

print 'end datasources'


print 'Create OSB Cluster'
cd('/')
create('OSBCluster', 'Cluster')

counter=0
for machine in HOSTS:
	counter=counter+1
	print 'Create OSB_Server' + str(counter)
	cd('/')
	create('OSB_Server'+str(counter), 'Server')
	changeManagedServer('OSB_Server'+str(counter),OSB_SERVER_PORT,machine)
	cd('/')
	assign('Server','OSB_Server'+str(counter),'Cluster','OSBCluster')
	print 'Add server groups OSB-MGD-SVRS-ONLY to OSB Server'
	serverGroup = ["OSB-MGD-SVRS-ONLY"]
	setServerGroups('OSB_Server'+str(counter), serverGroup)                      


print 'Updating Domain'
updateDomain()
print 'Domain Updated'

delete('osb_server1', 'Server')

print 'Adjusting File stores and tlogs'
cd('/ResourceGroupTemplates/OSBRuntimeResourceGroupTemplate/FileStores/FileStore')
cmo.setDirectory('/u01/oracle/runtime/test1domain/xbus-filestore')

cd('/ResourceGroupTemplates/OSBTemplate/FileStores/FileStore')
cmo.setDirectory('/u01/oracle/runtime/test1domain/rmfilestore')


counter=0
for machine in HOSTS:
	counter=counter+1
	cd('/FileStores/FileStore_auto_'+str(counter))
	cmo.setDirectory('/u01/oracle/runtime/test1domain/FileStore_auto_'+str(counter))



print 'Updating Domain'
updateDomain()
closeDomain();


print('Exiting...')
exit()



