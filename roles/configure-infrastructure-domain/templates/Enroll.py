connect('weblogic', '{{ weblogic_admin_pass }}', 't3://{{ inventory_hostname }}:{{ admin_server_port }}')
nmEnroll('{{ aserver_home }}') 
