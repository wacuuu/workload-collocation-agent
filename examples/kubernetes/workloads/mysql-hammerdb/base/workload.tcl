#!/bin/tclsh
proc runtimer { seconds } {
set x 0
set timerstop 0
while {!$timerstop} {
incr x
after 1000
  if { ![ expr {$x % 60} ] } {
          set y [ expr $x / 60 ]
          puts "Timer: $y minutes elapsed"
  }
update
if {  [ vucomplete ] || $x eq $seconds } { set timerstop 1 }
    }
return
}
dbset db mysql
diset connection mysql_host MYSQL_HOST
diset connection mysql_port 3306
diset tpcc mysql_user testuser
diset tpcc mysql_pass testpassword
diset tpcc mysql_driver timed
diset tpcc mysql_rampup 1
diset tpcc mysql_duration 60
print dict

loadscript
vuset vu VIRTUAL_USERS
vucreate
vurun
runtimer 60000
after 5000
