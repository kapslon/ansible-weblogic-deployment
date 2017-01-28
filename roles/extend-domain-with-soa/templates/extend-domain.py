WLHOME      = '{{ domains_location }}'
DOMAIN      = '{{ domain_name }}'
DOMAIN_PATH = '{{ aserver_home }}'
APP_PATH    = '{{ application_home }}'

HOSTS = {{ ansible_play_hosts }}
ADMIN_PASSWORD = '{{ weblogic_admin_pass }}'
ADMIN_SERVER   = 'AdminServer'
ADMIN_USER     = 'weblogic'

SERVER_ADDRESS = HOSTS[0]

SOA_SERVER_PORT = {{ soa_server_port }}

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

def changeDatasourceToAGL(datasource):
  print 'Change datasource '+datasource +' to AGL'
#  cd("/JDBCSystemResources/" + datasource + "/JdbcResource/" + datasource + "/JDBCOracleParams/" + datasource )
#  set("FanEnabled","true")
  cd("/JDBCSystemResource/" + datasource + "/JdbcResource/" + datasource )
  set("DatasourceType", "AGL")
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
print 'Adding SOA Template'
addTemplate('{{ oracle_home }}/soa/common/templates/wls/oracle.soa_template.jar')

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


print 'Create SOA Cluster'
cd('/')
create('SOACluster', 'Cluster')

counter=0
for machine in HOSTS:
	counter=counter+1
	print 'Create SOA_Server' + str(counter)
	cd('/')
	create('SOA_Server'+str(counter), 'Server')
	changeManagedServer('SOA_Server'+str(counter),SOA_SERVER_PORT,machine)
	cd('/')
	assign('Server','SOA_Server'+str(counter),'Cluster','SOACluster')
	print 'Add server groups SOA-MGD-SVRS-ONLY to SOA Server'
	serverGroup = ["SOA-MGD-SVRS-ONLY"]
	setServerGroups('SOA_Server'+str(counter), serverGroup)                      


print 'Updating Domain'
updateDomain()
print 'Domain Updated'

delete('soa_server1', 'Server')

print 'Adjusting File stores and tlogs'
cd('/FileStores/mds-soa')
cmo.setSynchronousWritePolicy('Direct-Write')
cmo.setDirectory('{{ jms_store_location }}/gmdsi/mds-soa')

counter=0
for machine in HOSTS:
	counter=counter+1
	cd('/FileStores/SOAJMSFileStore_auto_'+str(counter))
	cmo.setSynchronousWritePolicy('Direct-Write')
	cmo.setDirectory('{{ jms_store_location }}/SOAJMSFileStore_auto_'+str(counter))
	cd('/FileStores/UMSJMSFileStore_auto_'+str(counter))
	cmo.setSynchronousWritePolicy('Direct-Write')
	cmo.setDirectory('{{ jms_store_location }}/UMSJMSFileStore_auto_'+str(counter))
	cd('/FileStores/BPMJMSFileStore_auto_'+str(counter))
	cmo.setSynchronousWritePolicy('Direct-Write')
	cmo.setDirectory('{{ jms_store_location }}/BPMJMSFileStore_auto_'+str(counter))

changeDatasourceToXA('EDNDataSource')
changeDatasourceToXA('OraSDPMDataSource')
changeDatasourceToXA('SOADataSource')

print 'Updating Domain'
updateDomain()
closeDomain();


print('Exiting...')
exit()



