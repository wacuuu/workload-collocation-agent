#!/bin/bash
n=0
while (( $n < $1 ))
do
    $2
    let n+=1
done
echo "Stop-Cassandra-Stress-Now"