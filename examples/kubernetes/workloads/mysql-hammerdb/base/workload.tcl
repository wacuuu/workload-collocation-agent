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
diset tpcc mysql_timeprofile true
diset tpcc mysql_allwarehouse true
diset tpcc mysql_duration 1209600000
diset tpcc mysql_total_iterations 1000000000
print dict
loadscript

vuset vu VIRTUAL_USERS
vuset delay 500
vuset repeat 1209600000
vucreate
vurun

runtimer 1209600000
vudestroy
after 5000
