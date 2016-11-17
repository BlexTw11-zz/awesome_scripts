#!/bin/bash
#####################################################################
# Make your own binary upgrade file with unique date and timestamp! #
#####################################################################

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./make_upgrade_binary.sh </path/to/file.xe>"
    exit 1
fi

XTIMECOMPOSER=14.2
BOOTPARTITION_SIZE=0x30000

PATH_FILE=$1
FILE=${PATH_FILE##*/}
NOW=$(date +"%d%m%y-%H%M%S")
NAME="${FILE%.xe}-$NOW.bin"

xflash --factory-version $XTIMECOMPOSER --upgrade 1 $PATH_FILE --boot-partition-size $BOOTPARTITION_SIZE -o $NAME
