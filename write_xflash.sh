#!/bin/bash
#####################################################################
# Make your own binary upgrade file with unique date and timestamp! #
#####################################################################

if [ $# -eq 0 ]
  then
    echo "No arguments supplied"
    echo "Call ./write_xflash.sh </path/to/file.xe> <target>"
    exit 1
fi


TARGET=$2

if [ $TARGET == "C22" ]
then
    TARGET_FILE="SOMANET-C22.xn"
elif [ $TARGET == "C2X" ]
then
    TARGET_FILE="SOMANET-CoreC2X.xn"
else
    echo "Wrong target"
    echo "Use 'C22' or 'C2X'"
    exit 1
fi

XTIMECOMPOSER=14.3

PATH_FILE=$1
TARGET_PATH="targets"
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")


xflash --write-all $PATH_FILE --target-file $SCRIPTPATH/$TARGET_PATH/$TARGET_FILE

