#!/bin/bash

####################################################
# Make firmware update over ethernet the easy way! #
####################################################

NODE_IP=192.168.0.1
MASTER_IP=192.168.0.2
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

IF_NAME=`ifconfig | grep -oe "^e[nt][a-z0-9]*"

# Set temporary new IP address`
`sudo ifconfig $IF_NAME $MASTER_IP`

BINARY=$1

${TFTP} $NODE_IP << !
mode binary
put  $BINARY
quit
!
# Reset IP address from interface
`sudo ifconfig $IF_NAME 0.0.0.0`
