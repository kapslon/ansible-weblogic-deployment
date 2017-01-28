#!/bin/bash

#######################################################################
#
#                   midct.sh
#       Author: G. Lysko
#       Description: Middelware start stop scripts wrapper. Based on several other scripts. 
#       Version: 0.1
#       Change Log:
#               2016.11.18 - G.Lysko Initial version
#		
#
#
#
#######################################################################

export SRC_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CFG_FILENAME="${SRC_DIR}/config/midctl_$(hostname).cfg"
WL_START_LOG_FILENAME="${SRC_DIR}/log/middlewareControlUsage.log"
DEBUG=FALSE


if [ ! -e  $CFG_FILENAME ]; then
	CFG_FILENAME="${SRC_DIR}/config/midctl_$(hostname | cut -d"." -f1).cfg"
fi

#some functions for coloured output:

function echoWarn(){
    echo -e '\033[1;30m'$1'\033[1;m'
    echo "$(date): WARN : ${1}" >> $WL_START_LOG_FILENAME
}

function echoAction(){
    echo -e '\033[1;32m'$1'\033[1;m'
    echo "$(date): ACTION : ${1}" >> $WL_START_LOG_FILENAME
}

function echoInfo(){
    echo -e '\033[1;33m'$1'\033[1;m'
    echo "$(date): INFO : ${1}" >> $WL_START_LOG_FILENAME
}

function echoDebug(){
    if [ $DEBUG == "TRUE" ]; then 
	>&2 echo -e '\033[1;33m' "$1" '\033[1;m'
    fi
}

function echoError(){
    echo -e '\033[0;31m' "$1" '\033[0m'
    echo "$(date): ERROR : ${1}" >> $WL_START_LOG_FILENAME
}

function NodeManagerStatus() {
	echoDebug "Check nm status"
	listening=$(netstat -nlp | grep ":$1" | grep java | wc -l 2> /dev/null)
	match=1
	if [ "$listening" -gt 0 ]; then
		return 0
	else
		return 1
	fi
}


function usage() {
	echoInfo "Usage:"
	echoInfo "./$0 <start/stop/status>"
	echoInfo "./$0 <start/stop/status> ComponentList"
}

function NodeManagerComponentAction() {
	action=$1
	component=$2
	main_component=$(cut -d '-' -f -2 <<< $component)
	
	NM_START_LOC=`grep -m 1 "^$main_component-home" $CFG_FILENAME | cut -d '=' -f 2`
	NM_PORT=`grep -m 1 "^$main_component-port" $CFG_FILENAME | cut -d '=' -f 2`
	if [ ${#NM_START_LOC} -gt 1 ]; then 
		case "$action" in
			"start")
				NodeManagerStatus $NM_PORT
				if [ $? -ne 0 ] && [ -e "${NM_START_LOC}/startNodeManager.sh" ]; then
					echoInfo "NM startup script exists, Starting"
					nohup ${NM_START_LOC}/startNodeManager.sh &
					count=0
					while [ $count -lt 20 ]; do
						NodeManagerStatus $NM_PORT
		                                if [ $? -eq 0 ]; then
							return 0
						fi
						echoInfo "NM not ready yet"
						sleep 15
						count=$(expr  $count + 1)
					done
				else
					echoError "NM startup script doesen't exists or NM already running"
				fi
			;;
			"stop")
				NodeManagerStatus $NM_PORT
				if [ $? -eq 0 ] && [ -e "${NM_START_LOC}/stopNodeManager.sh" ]; then
					echoInfo "NM stop script exists, Stoping"
					${NM_START_LOC}/stopNodeManager.sh
				else
					echoError "NM stop script doesen't exists or Node manger already stoped"
				fi
			;;
			"status")
				NodeManagerStatus $NM_PORT
				if [ $? -ne 0 ]; then
					echoError "Node Manager process not there"
				else
					echoAction "Node Manager process working"
				fi
			;;
			*)
				echoError "Wrong option $2"
				esac
	else 
		echoError "Missing nodemanager startup script location"
		return 1
	fi

}

function buildComponentList() {
	input_component_list=$1
	configured_components="$(cat $CFG_FILENAME | awk '{match($0,/(.*)-serverName=(.*)/,output); print output[1]}' | sort | uniq)"
	echoDebug "Configured components: $configured_components"
	new_component_list=""
	input_component_list=$(echo $input_component_list | tr ',' '\n')
	echoDebug "input component list: $input_component_list"
	for component in $input_component_list; do
		resolved_component=$(grep -e "$component" <<< "$configured_components")
		echoDebug "Resolved component $resolved_component"
		new_component_list="$new_component_list $resolved_component"
	done
	echoDebug "Resolved component list: $new_component_list"
	echo $new_component_list | grep -v '^$' | tr '\n' ' '   
}

function WeblogicComponentAction() {
	component=$2
	action=$1
	main_component=$(cut -d '-' -f -2 <<< $component)
	OSUSER=`grep -m 1 "^$main_component-osUser" $CFG_FILENAME | cut -d '=' -f 2`
	WLST=`grep -m 1 "^$main_component-wlsEnvironment" $CFG_FILENAME | cut -d '=' -f 2`
	DOMAIN=$(cut -d '-' -f 2 <<< $component)
	SERVERNAME=$(cut -d '-' -f 3 <<< $component)
	su_cmd=""
	if [ `whoami` != "$OSUSER" ]; then
		su_cmd="sudo su - $OSUSER -c "
	fi
	echoAction "Executing $su_cmd $WLST $SRC_DIR/control_weblogic.py $action WebLogic $DOMAIN $SERVERNAME"
	if [ $action == "status" ]; then 
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action WebLogic $DOMAIN $SERVERNAME | grep "in state"
		return ${PIPESTATUS[0]}
	else
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action WebLogic $DOMAIN $SERVERNAME 
	fi
}

function OhsComponentAction() {
        component=$2
        action=$1
	main_component=$(cut -d '-' -f -2 <<< $component)
	OSUSER=`grep -m 1 "^$main_component-osUser" $CFG_FILENAME | cut -d '=' -f 2`
	WLST=`grep -m 1 "^$main_component-wlsEnvironment" $CFG_FILENAME | cut -d '=' -f 2`
        DOMAIN=$(cut -d '-' -f 2 <<< $component)
        SERVERNAME=$(cut -d '-' -f 3 <<< $component)
        su_cmd=""
        if [ `whoami` != "$OSUSER" ]; then
                su_cmd="sudo su - $OSUSER -c "
        fi
	echoAction "Executing $su_cmd $WLST $SRC_DIR/control_weblogic.py $action OHS $DOMAIN $SERVERNAME"
	if [ $action == "status" ]; then 
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action OHS $DOMAIN $SERVERNAME | grep "in state"
		return ${PIPESTATUS[0]}
	else	
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action OHS $DOMAIN $SERVERNAME
	fi
}

function ReportsServerComponentAction() {
        component=$2
        action=$1
	main_component=$(cut -d '-' -f -2 <<< $component)
	OSUSER=`grep -m 1 "^$main_component-osUser" $CFG_FILENAME | cut -d '=' -f 2`
	WLST=`grep -m 1 "^$main_component-wlsEnvironment" $CFG_FILENAME | cut -d '=' -f 2`
        DOMAIN=$(cut -d '-' -f 2 <<< $component)
        SERVERNAME=$(cut -d '-' -f 3 <<< $component)
        su_cmd=""
        if [ `whoami` != "$OSUSER" ]; then
                su_cmd="sudo su - $OSUSER -c "
        fi
	echoAction "Executing $su_cmd $WLST $SRC_DIR/control_weblogic.py $action ReportsServerComponent $DOMAIN $SERVERNAME"
	if [ $action == "status" ]; then 
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action ReportsServerComponent $DOMAIN $SERVERNAME | grep "in state"
		return ${PIPESTATUS[0]}
	else	
		$su_cmd $WLST $SRC_DIR/control_weblogic.py $action ReportsServerComponent $DOMAIN $SERVERNAME
	fi
}


EXECUTED=''



echoAction "Script execution by $(who am i) as $(whoami)"

	
if [ -e  $CFG_FILENAME ]; then
	echoInfo "Config File Exists: $CFG_FILENAME"
	COMPONENT_LIST=`grep -m 1 "^hostedComponents" $CFG_FILENAME | cut -d '=' -f 2 | tr ',' ' '`
	#Reverse order for stop
	if [ "$1" == "stop" ]; then
		echoDebug "Reversing Components list"
		COMPONENT_LIST="$(echo "$COMPONENT_LIST" | tr ' ' '\n' | tac | tr '\n' ' ')"
	fi
	if [ ${#COMPONENT_LIST} -gt 1 ]; then
		echoDebug "$HOSTED_APPS has valid length ${#COMPONENT_LIST} "
		echoDebug "Number of Arguments is $#"
		#CHECK INVOCATION STATE:
		if [ "$#" -lt 1  ];then
			# raise error when not exactely 3 parameters arrive
			echoError "no valid input given - need at least 1 parameter"
			usage
			exit 1;
		fi
		if [ "$#" -gt 2  ];then
			echoError "no valid input given - need less then 2 parameters"
			usage
			exit 1;
		fi
		# Adjust component list
		if [ "$#" -eq 2  ]; then
			COMPONENT_LIST="$(buildComponentList $2)"
		fi
		if [ ${#COMPONENT_LIST} -lt 2 ]; then
			echoError "Lack of matcing components"
		fi

		echoDebug "Component list: ${COMPONENT_LIST} "
		for component in $COMPONENT_LIST; do
			echoDebug "Action for  $component"
			case $component in
				WebLogic* )
					WeblogicComponentAction $1 $component
				;;
				NodeManager* )
					echo "noide"
					NodeManagerComponentAction $1 $component
				;;
				OHS* )
					OhsComponentAction $1 $component
				;;
				ReportsServerComponent* )
					ReportsServerComponentAction $1 $component
				;;
				*)
					echoError " Wrong component type $component"
			esac
		done
	else
		echoError "hostedComponents list empty"
	fi

else
	echoError "Missing $CFG_FILENAME"

fi


