#!/bin/bash
################################################
# Erase your CORE module with this nice script #
################################################

TARGET_PATH="targets"


if [ $# -eq 0 ]
then
    echo "No target supplied"
    echo "Call $0 <target>"
    exit 1
fi

TARGET=$1


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


SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

echo "Delete target: " $TARGET

# Erase chip
xflash --erase-all --target-file $SCRIPTPATH/$TARGET_PATH/$TARGET_FILE
echo "done...exit"
