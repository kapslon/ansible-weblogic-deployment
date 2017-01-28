#######################################################################
#
#                   control_weblogic.py
#       Author: G. Lysko
#       Description: Creates wlst connection and start/stops servers. Based on other scripts
#       Version: 0.1
#       Change Log:
#               2016.11.18 - G.Lysko Initial version
#
#
#
#######################################################################




# Start Server
import sys
import os
import socket
#import datetime
from java.util import Properties
from java.io import FileInputStream
from java.io import File

domainProps = Properties();
adminURL = '';
userConfigFile = '';
userKeyFile = '';
processingMode='';
domain='';
domain_home='';
servername='';
propertyFilename='';
nodemanager_home='';
#src_dir=(os.environ['SRC_DIR'])
try:
	src_dir=(os.environ['SRC_DIR'])
except:
	src_dir=os.path.abspath(os.path.dirname(sys.argv[0]))+'/'

logfile_name=src_dir + '/log/middlewareControlUsage.log'

# ================================================================
# initialize properties - get all relevant information from config file
# ================================================================

def intialize():
    global domainProps;
    global userConfigFile;
    global userKeyFile;
    global adminURL;
    global processingMode;
    global domain;
    global domain_home;
    global nodemanager_home;
    global nodemanager_port;
    global nodemanagerUserConfigFile;
    global nodemanagerUserKeyFile;
    global servername;
    global propertyFilename;
    global serverType;

    
    try:
        hostname=str(socket.gethostname()).replace(".*","")
        domainProps = Properties()
	if os.path.isfile(src_dir+'/config/midctl_'+ hostname+".cfg") == false :
		hostname=hostname.split('.')[0]
	propertyFilename=src_dir+'/config/midctl_'+ hostname+".cfg"
        input = FileInputStream(propertyFilename)
        domainProps.load(input)
        input.close()
        #initialize domain, servername, processing mode from parameters:
        processingMode=sys.argv[1]
        serverType=sys.argv[2]
        domain=sys.argv[3]
        servername=sys.argv[4]
        propertyPrefix=serverType+"-"+sys.argv[1]+"-"+sys.argv[2]+"-"
        # extract required properties from config file
        nodemanager_home=domainProps.get('NodeManager-'+domain+'-home')
	nodemanager_port=domainProps.get('NodeManager-'+domain+'-port')
	nodemanagerUserConfigFile=domainProps.get('NodeManager-'+domain+'-NodeUserConfigFile')
	nodemanagerUserKeyFile=domainProps.get('NodeManager-'+domain+'-NodeUserKeyFile')
	if nodemanager_port is None:
		nodemanager_port=5556
        domain_home=domainProps.get(serverType+"-"+domain+'-domainHome')
        if ( domainProps.get(serverType+"-"+domain+'-'+servername+'-domainHome') != "" ):
		domain_home=domainProps.get(serverType+"-"+domain+'-'+servername+'-domainHome')
        adminURL= domainProps.get(serverType+"-"+domain+'-adminUrl')
        userConfigFile = domainProps.get(serverType+"-"+domain+'-AdminUserConfigFile')
        userKeyFile =  domainProps.get(serverType+"-"+domain+'-AdminUserKeyFile')
        print highlightInfo('init script for command: ' + processingMode +' serverName: ' + servername + ' on host: ' + hostname + nodemanagerUserConfigFile)
    except:
        print highlightError('Cannot load properties  '+propertyFilename+ '!');
        exit();

# ================================================================
#   define colour highlighting for readability
# ================================================================

def writeToLog(string,entry):
	import time
	f = open(logfile_name,'a')
	f.write("%s : %s :%s \n" %(time.strftime("%a %b %d %H:%M:%S %Z %Y"),entry,string))
	f.close()

def highlightWarn(string):
	writeToLog(string,'WARN')
        return "\033[1;30m" + string + "\033[1;m"
def highlightAction(string):
	writeToLog(string,'ACTION')
        return "\033[1;32m" + string + "\033[1;m"
def highlightInfo(string):
	writeToLog(string,'INFO')
        return "\033[1;33m" + string + "\033[1;m"
def highlightError(string):
	writeToLog(string,'ERROR')
        return "\033[1;31m" + string + "\033[1;m"

# ================================================================
#   CHECK if desired command can be executed:
#   If Server is down - only start is permitted
#   If Server is NOT down - only stop is permitted
# ================================================================

def isprocessingModeAllowedInServerState(processingMode, serverstate):
    if (processingMode == 'stop'):
     if (serverstate == "SHUTDOWN") or (serverstate == "FAILED_NOT_RESTARTABLE") or (serverstate == "SHUTTING_DOWN"):
        print highlightError('processingMode: ' + processingMode + ' not supported in serverstate: ' + serverstate)
        return false
     else:
        return true
    elif (processingMode == 'start'):
     if (serverstate == "SHUTDOWN") or (serverstate == "FAILED_NOT_RESTARTABLE") or (serverstate == "UNKNOWN"):
        return true
     else:
        print highlightError('processingMode: ' + processingMode + ' not supported in serverstate: ' + serverstate)
        return false
    else:
        print highlightError('processingMode: ' + processingMode + ' not supported ')
        return false
 
def executeServerLifecycleCommand():
     connUri = adminURL
     currentcount = 0;
     host = str(socket.gethostname());
     adminServerIsRunning = 'false';
     nodeManagerIsRunning = 'false';
    # ================================================================
    #   TRY Adminserver FIRST
    # ================================================================
     if connUri is not None and servername!='AdminServer':
	 while ((adminServerIsRunning=='false')  and (currentcount<3)):
	   try:
		print highlightInfo ('Connecting to the Admin Server ('+connUri+')');
		connect(userConfigFile=userConfigFile,userKeyFile=userKeyFile,url=connUri);
		adminServerIsRunning = 'true';
		print highlightInfo('Connected to admin ');
		try:
		    domainRuntime()
		    cd ('ServerLifeCycleRuntimes/'+servername)
		    serverstate=cmo.getState();
		    if processingMode == 'status':
			print highlightInfo('server: ' + servername + ' in state: ' + serverstate)
			if (serverstate=='RUNNING'):
			    sys.exit(0);
			else:
			    sys.exit(1);
		    elif processingMode == 'stop':
			if (isprocessingModeAllowedInServerState(processingMode, serverstate)):
			    shutdown(servername,'Server','true',1000,force='true', block='true')
			    print highlightAction( 'shutdown server: ' + servername)
			    sys.exit(0);
			else:
			    sys.exit(1);
		    elif processingMode == 'start':
			if (isprocessingModeAllowedInServerState(processingMode, serverstate)):
			    start(servername,"Server")
			    print highlightAction( 'start server: ' + servername)
			    sys.exit(0);
			else:
			    sys.exit(1);
		    serverstate=cmo.getState();
		    print highlightInfo ('server ' + servername +' is in now state ' +serverstate);
		    exit();
		except SystemExit:
		    raise
		except:
		    print highlightError('Error while trying to execute command on AdminServer')
		    print "Unexpected error:", sys.exc_info();
		    print traceback.print_stack();
	   except SystemExit:
		raise
	   except:
		print highlightInfo('AdminServer is (not yet) running. Will wait for 10sec.');
		print dumpStack();
		java.lang.Thread.sleep(1000);
		currentcount = currentcount +1;
	 currentcount = 0;
    # ================================================================
    #   IF AdminServer not reachable try nodemanager
    # ================================================================
     while ((nodeManagerIsRunning=='false') and (currentcount<3)):   
        try:     
             if (nodeManagerIsRunning=='false'):
                    print highlightInfo ('Connecting to the Node Manager');
                    nmConnect(userConfigFile=nodemanagerUserConfigFile,userKeyFile=nodemanagerUserKeyFile,host=host,port=nodemanager_port,domainName=domain,domainDir=domain_home);
                    nodeManagerIsRunning='true'
                    try:
                        serverstate=nmServerStatus(servername,serverType=serverType);
                        if processingMode == 'status':
                            print highlightInfo('server: ' + servername + ' in state: ' + serverstate);
                            if (serverstate=='RUNNING'):
                                sys.exit(0);
                            else:
                                sys.exit(1);
                        elif processingMode == 'stop':
                            if (isprocessingModeAllowedInServerState(processingMode, serverstate)):
                                nmKill(servername,serverType=serverType)
                                print highlightInfo('shutdown server: ' + servername);
                                exit();
                            else:
                                exit();
                        elif processingMode == 'start':
                            if (isprocessingModeAllowedInServerState(processingMode, serverstate)):
                                nmStart(servername,serverType=serverType);
                                print highlightInfo('start server: ' + servername);
                                exit();
                            else:
                                exit();
                        print highlightInfo('server ' + servername +' is in state ' +serverstate);
                        exit();
                    except SystemExit:
                        raise 
                    except:
                        print highlightError('Error while trying to execute command on Nodemanager')   
             sys.exit(1);
        except SystemExit:
            raise
        except:
            print highlightInfo('Nodemanager is (not yet) running. Will wait for 10sec.');
            dumpStack();
            java.lang.Thread.sleep(1000);
            currentcount = currentcount +1;
     print highlightInfo('server: ' + servername + ' in state: UNKNONOWN - Unable to connect to NM or Admin Server');sys.exit(1);
     sys.exit(1);
            

# ================================================================
#           Main Code Execution
# ================================================================

if __name__== "main":
        # test argument
	if not logfile_name:
		print 'Log location not set - Please set enviromental variable - WL_START_LOG_FILENAME'
		exit();

        if len(sys.argv) < 3:
            print highlightInfo('Usage:  scriptname.py  <domain> <serverName> <start/stop/status>');
            exit();

        intialize();
        executeServerLifecycleCommand();
 
