#!/bin/bash
# Usage: ./flash_contelec <BIN-FILE>

if [ $# -eq 0 ]
then
    echo "No arguments supplied"
    echo "Call ./flash_contelec.sh <binary>"
    exit 1
fi

BIN=$1
CONTELEC_DEV="LPC1112"

JLinkExe -Device $CONTELEC_DEV -if SWD -speed 4000 << ! 
connect
loadfile $BIN
exit
!
