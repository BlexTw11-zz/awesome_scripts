#!/bin/bash
#####################################################################
# Make your own binary upgrade file with unique date and timestamp! #
#####################################################################

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./make_upgrade_binary.sh </path/to/file.xe> [<output_name>]"
    exit 1
fi

if [ $# -eq 2 ]
  then
    INPUT_NAME=$2
fi

XTIMECOMPOSER=14.2
BOOTPARTITION_SIZE=0x30000

PATH_FILE=$1
FILE=${PATH_FILE##*/}
NOW=$(date +"%y%m%d-%H%M%S")

if [ $INPUT_NAME ]; then
    NAME="$INPUT_NAME-$NOW.bin"
else
    NAME="${FILE%.xe}-$NOW.bin"
fi

echo "Name:" $NAME

xflash --factory-version $XTIMECOMPOSER --upgrade 1 $PATH_FILE --boot-partition-size $BOOTPARTITION_SIZE -o $NAME
