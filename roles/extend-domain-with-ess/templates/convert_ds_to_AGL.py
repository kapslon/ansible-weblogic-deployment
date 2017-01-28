WLHOME      = '{{ domains_location }}'
DOMAIN      = '{{ domain_name }}'
DOMAIN_PATH = '{{ aserver_home }}'
APP_PATH    = '{{ application_home }}'

HOSTS = {{ ansible_play_hosts }}
ADMIN_PASSWORD = '{{ weblogic_admin_pass }}'
ADMIN_SERVER   = 'AdminServer'
ADMIN_USER     = 'weblogic'

def changeDatasourceToAGL(datasource):
  print 'Change datasource '+datasource +' to AGL'
  cd("/JDBCSystemResource/" + datasource + "/JdbcResource/" + datasource )
  set("DatasourceType", "AGL")
  cd('/')

readDomain(DOMAIN_PATH)

cd('/JDBCSystemResource/')
dsList=ls(returnMap='true')
for ds in dsList:
        changeDatasourceToAGL(ds)


print 'Updating Domain'
updateDomain()
closeDomain();


print('Exiting...')
exit()



