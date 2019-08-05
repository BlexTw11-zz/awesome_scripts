#!/bin/bash

####################################################
# Make firmware update over ethernet the easy way! #
####################################################

NODE_IP=192.168.0.11
MASTER_IP=192.168.0.2
IF=enx3c18a0099d3c

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
    echo "Call $0 </path/to/binary>"
    exit 1
fi

if [ $# -eq 2 ]
then
    IF_NAME=$2
else
    IF_NAME=$IF
fi

GET_IP=`ip -4 addr show $IF_NAME | grep -oP '(?<=inet\s)\d+(\.\d+){3}'`
tmp_ip=${GET_IP}

# Set temporary new IP address`
`sudo ifconfig $IF_NAME $MASTER_IP`

BINARY=$1

${TFTP} $NODE_IP << EOF
mode binary
timeout 5
put $BINARY
quit
EOF

# Reset IP address from interface
`sudo ifconfig $IF_NAME $tmp_ip`
`sudo ifconfig $IF_NAME down`
`sudo ifconfig $IF_NAME up`

echo "Quit"
exit 0
