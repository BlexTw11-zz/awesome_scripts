#!/bin/bash
#####################################################
# Flash new firmware on REM-16MT (Contelec) sensor. #
# Usage: ./flash_contelec <BIN-FILE>                #
#####################################################

CONTELEC_DEV="LPC1112"

JLINK=`which JLinkExe`


if [ -z ${JLINK} ]
then
   echo "Error: JLinkExe is not installed"
   echo "Download it from: https://www.segger.com/downloads/jlink/JLink_Linux_V616j_x86_64.deb"
   exit 1
fi

if [ $# -eq 0 ]
then
    echo "No arguments supplied"
    echo "Call ./flash_contelec.sh </path/to/binary>"
    exit 1
fi

echo "Wait 5 seconds. Connect now the pinheader to the sensor"
sleep 5
# Save binary path
BIN=$1


${JLINK} -Device $CONTELEC_DEV -if SWD -speed 4000 << ! 
connect
loadfile $BIN
exit
!
