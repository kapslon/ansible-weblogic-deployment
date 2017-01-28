WLHOME      = '{{ domains_location }}'
DOMAIN      = '{{ domain_name }}'
DOMAIN_PATH = '{{ aserver_home }}'
APP_PATH    = '{{ application_home }}'

HOSTS = {{ ansible_play_hosts }}
ADMIN_PASSWORD = '{{ weblogic_admin_pass }}'
ADMIN_SERVER   = 'AdminServer'
ADMIN_USER     = 'weblogic'

SERVER_ADDRESS = HOSTS[0]

ESS_SERVER_PORT = {{ ess_server_port }}

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
print 'Adding ESS Template'
addTemplate('{{ oracle_home }}/oracle_common/common/templates/wls/oracle.ess.basic_template.jar')
addTemplate('{{ oracle_home }}/em/common/templates/wls/oracle.em_ess_template.jar')

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


print 'Create ESS Cluster'
cd('/')
create('ESSCluster', 'Cluster')

counter=0
for machine in HOSTS:
	counter=counter+1
	print 'Create ESS_Server' + str(counter)
	cd('/')
	create('ESS_Server'+str(counter), 'Server')
	changeManagedServer('ESS_Server'+str(counter),ESS_SERVER_PORT,machine)
	cd('/')
	assign('Server','ESS_Server'+str(counter),'Cluster','ESSCluster')
	print 'ESS-MGD-SVRS to ESS Server'
	serverGroup = ["ESS-MGD-SVRS"]
	setServerGroups('ESS_Server'+str(counter), serverGroup)                      


print 'Updating Domain'
updateDomain()
print 'Domain Updated'

delete('ess_server1', 'Server')

print 'Adjusting File stores'
cd('/FileStores/mds-ESS_MDS_DS')
cmo.setSynchronousWritePolicy('Direct-Write')
cmo.setDirectory('/u01/oracle/runtime/test1domain/store/gmds/mds-ESS_MDS_DS')

print 'Updating Domain'
updateDomain()
closeDomain();


print('Exiting...')
exit()



