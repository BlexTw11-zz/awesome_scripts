#!/bin/bash

####################################################
# Make firmware update over ethernet the easy way! #
####################################################

TFTP=`which tftp`

if [ -z ${TFTP} ]
then
   echo "Error: tftp is not installed"
   exit 1
fi

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./make_ethernet_update.sh <binary>"
    exit 1
fi

NODE_IP=192.168.0.1
BINARY=$1

${TFTP} $NODE_IP << !
mode binary
put  $BINARY
quit
!
