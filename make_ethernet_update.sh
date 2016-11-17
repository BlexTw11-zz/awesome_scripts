#!/bin/bash

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./make_ethernet_update.sh <binary>"
    exit 1
fi

NODE_IP=192.168.0.1
BINARY=$1

tftp $NODE_IP << !
mode binary
put  $BINARY
quit
!
