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


PATH_FILE=$1
if [ $# -eq 2 ]
then
    TARGET=$2

    if [ $TARGET == "c22" ]
    then
        TARGET_FILE="SOMANET-C22.xn"
    elif [ $TARGET == "c2x" ]
    then
        TARGET_FILE="SOMANET-CoreC2X.xn"
    else    
        echo "Wrong target"
        echo "Use 'c22' or 'c2x'"
        exit 1
    fi
else
    TARGET_FILE="SOMANET-CoreC2X.xn"
fi

XTIMECOMPOSER=14.3

TARGET_PATH="targets"
SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")


xflash --write-all $PATH_FILE --target-file $SCRIPTPATH/$TARGET_PATH/$TARGET_FILE

