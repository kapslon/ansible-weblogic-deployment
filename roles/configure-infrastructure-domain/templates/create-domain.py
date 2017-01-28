WLHOME      = '{{ domains_location }}'
DOMAIN      = '{{ domain_name }}'
DOMAIN_PATH = '{{ aserver_home }}'
APP_PATH    = '{{ application_home }}'

HOSTS = {{ ansible_play_hosts }}
ADMIN_PASSWORD = '{{ weblogic_admin_pass }}'
ADMIN_SERVER   = 'AdminServer'
ADMIN_USER     = 'weblogic'

SERVER_ADDRESS = HOSTS[0]

ADMIN_SERVER_PORT = {{ admin_server_port }}
OWSM_SERVER_PORT = {{ owsm_server_port }}

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

def createBootPropertiesFile(directoryPath,fileName, username, password):
  serverDir = File(directoryPath)
  bool = serverDir.mkdirs()
  fileNew=open(directoryPath + '/'+fileName, 'w')
  fileNew.write('username=%s\n' % username)
  fileNew.write('password=%s\n' % password)
  fileNew.flush()
  fileNew.close()

def createAdminStartupPropertiesFile(directoryPath, args):
  adminserverDir = File(directoryPath)
  bool = adminserverDir.mkdirs()
  fileNew=open(directoryPath + '/startup.properties', 'w')
  args=args.replace(':','\\:')
  args=args.replace('=','\\=')
  fileNew.write('Arguments=%s\n' % args)
  fileNew.flush()
  fileNew.close()

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


print('Start...wls domain with template {{ wl_home }}/common/templates/wls/wls.jar')
readTemplate('{{ wl_home }}/common/templates/wls/wls.jar')


cd('/')

print('Set domain log')
create('base_domain','Log')

cd('/Log/base_domain')
set('FileCount'   ,10)
set('FileMinSize' ,5000)
set('RotationType','byTime')
set('FileTimeSpan',24)

cd('/Servers/AdminServer')
# name of adminserver
set('Name',ADMIN_SERVER )
cd('/Servers/'+ADMIN_SERVER)
set('ListenAddress',SERVER_ADDRESS)
set('ListenPort'   ,ADMIN_SERVER_PORT)

setOption( "AppDir", APP_PATH )

create(ADMIN_SERVER,'ServerStart')
cd('ServerStart/'+ADMIN_SERVER)
set('JavaVendor','Sun')
set('JavaHome'  , JAVA_HOME)

cd('/Server/'+ADMIN_SERVER)
create(ADMIN_SERVER,'SSL')
cd('SSL/'+ADMIN_SERVER)
set('Enabled'                    , 'False')
set('HostNameVerificationIgnored', 'True')

if JSSE_ENABLED == true:
  set('JSSEEnabled','True')
else:
  set('JSSEEnabled','False')


cd('/Server/'+ADMIN_SERVER)

create(ADMIN_SERVER,'Log')
cd('/Server/'+ADMIN_SERVER+'/Log/'+ADMIN_SERVER)
set('FileCount'   ,10)
set('FileMinSize' ,5000)
set('RotationType','byTime')
set('FileTimeSpan',24)

print('Set password...')
cd('/')
cd('Security/base_domain/User/weblogic')

# weblogic user name + password
set('Name',ADMIN_USER)
cmo.setPassword(ADMIN_PASSWORD)

if DEVELOPMENT_MODE == true:
  setOption('ServerStartMode', 'dev')
else:
  setOption('ServerStartMode', 'prod')

setOption('JavaHome', JAVA_HOME)

print('write domain...')
# write path + domain name
writeDomain(DOMAIN_PATH)
closeTemplate()

createBootPropertiesFile(DOMAIN_PATH+'/servers/'+ADMIN_SERVER+'/security','boot.properties',ADMIN_USER,ADMIN_PASSWORD)
createBootPropertiesFile(DOMAIN_PATH+'/config/nodemanager','nm_password.properties',ADMIN_USER,ADMIN_PASSWORD)

es = encrypt(ADMIN_PASSWORD,DOMAIN_PATH)

readDomain(DOMAIN_PATH)

print('set domain password...') 
cd('/SecurityConfiguration/'+DOMAIN)
set('CredentialEncrypted',es)

print('Set nodemanager password')
set('NodeManagerUsername'         ,ADMIN_USER )
set('NodeManagerPasswordEncrypted',es )

cd('/')

setOption( "AppDir", APP_PATH )

print 'Adding Templates'
addTemplate('{{ oracle_home }}/oracle_common/common/templates/wls/oracle.wls-webservice-template.jar')
addTemplate('{{ oracle_home }}/oracle_common/common/templates/wls/oracle.wsmpm_template.jar')
addTemplate('{{ oracle_home }}/oracle_common/common/templates/wls/oracle.applcore.model.stub_template.jar')


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

for machine in HOSTS:
	print('Create machine ' + machine + ' with type UnixMachine')
	cd('/')
	create(machine,'UnixMachine')
	cd('UnixMachine/'+machine)
	create(machine,'NodeManager')
	cd('NodeManager/'+machine)
	set('ListenAddress',machine)

print 'Change AdminServer'
cd('/Servers/'+ADMIN_SERVER)
set('Machine',SERVER_ADDRESS)

print 'Create WSM Cluster'
cd('/')
create('OwsmCluster', 'Cluster')

counter=0
for machine in HOSTS:
	counter=counter+1
	print 'Create Owsm_Server' + str(counter)
	cd('/')
	create('Owsm_Server'+str(counter), 'Server')
	changeManagedServer('Owsm_Server'+str(counter),OWSM_SERVER_PORT,machine)
	cd('/')
	assign('Server','Owsm_Server'+str(counter),'Cluster','OwsmCluster')
	print 'Add server groups JRF-MAN-SVR, WSM-CACHE-SVR, WSMPM-MAN-SVR to OWSM Server'
	serverGroup = ["JRF-MAN-SVR", "WSM-CACHE-SVR", "WSMPM-MAN-SVR"]
	setServerGroups('Owsm_Server'+str(counter), serverGroup)                      


print 'Updating Domain'
updateDomain()
print 'Domain Updated'

print 'Adjusting File stores'
cd('/FileStores/mds-owsm')
cmo.setSynchronousWritePolicy('Direct-Write')
cmo.setDirectory('{{ jms_store_location }}/gmds')

cd('/FileStores/WseeFileStore')
cmo.setSynchronousWritePolicy('Direct-Write')
cmo.setDirectory('{{ jms_store_location }}/WseeFileStore')

counter=0
for machine in HOSTS:
	counter=counter+1
	cd('/FileStores/WseeFileStore_auto_'+str(counter))
	cmo.setSynchronousWritePolicy('Direct-Write')
	cmo.setDirectory('{{ jms_store_location }}/WseeFileStore_auto_'+str(counter))


print 'Updating Domain'
updateDomain()
closeDomain();


print('Exiting...')
exit()



