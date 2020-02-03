#!/bin/tclsh
puts "SETTING CONFIGURATION"
global complete
proc wait_to_complete {} {
global complete
set complete [vucomplete]
if {!$complete} { after 5000 wait_to_complete } else { exit }
}
dbset db mysql
diset connection mysql_host MYSQL_HOST
diset connection mysql_port 3306
diset tpcc mysql_user testuser
diset tpcc mysql_pass testpassword
diset tpcc mysql_count_ware COUNT_WARE
diset tpcc mysql_partition true
diset tpcc mysql_num_vu VIRTUAL_USERS_BUILD
diset tpcc mysql_storage_engine STORAGE_ENGINE
print dict
buildschema
wait_to_complete
vwait forever
