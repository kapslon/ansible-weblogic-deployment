#!/bin/bash

SCRIPT=$(readlink -f $0)
SCRIPT_PATH=$(dirname $SCRIPT)

JAVA_HOME={{ java_home }}
export JAVA_HOME

{{ oracle_home }}/oracle_common/bin/rcu -silent -responseFile {{ software_location }}/rcu.soa.rsp  -f < {{ software_location }}/rcu.passwd.txt
