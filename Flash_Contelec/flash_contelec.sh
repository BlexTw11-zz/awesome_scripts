#!/bin/bash
# Usage: ./flash_contelec <BIN-FILE>

BIN=$1
CONTELEC_DEV="LPC1112"

JLinkExe -Device $CONTELEC_DEV -if SWD -speed 4000 << ! 
connect
loadfile $BIN
exit
!
