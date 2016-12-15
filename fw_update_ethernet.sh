#!/bin/bash

####################################################
# Make firmware update over ethernet the easy way! #
####################################################

NODE_IP=192.168.0.1
MASTER_IP=192.168.0.2

# Check if tftp is installed
TFTP=`which tftp`
if [ -z ${TFTP} ]
then
   echo "Error: tftp is not installed"
   exit 1
fi

# Check if path to binary is supplied
if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./make_ethernet_update.sh </path/to/binary>"
    exit 1
fi

IF_NAME=`ifconfig | grep -oe "^e[nt][a-z0-9]*"`
for i in $IF_NAME; do lastInterface=$i; done;
IF_NAME=$lastInterface

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
# Don't know if necessary
`sudo dhclient $IF_NAME`
