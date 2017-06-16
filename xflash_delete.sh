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


if [ $TARGET == "C22" ] 
then
    TARGET_FILE="SOMANET-C22.xn"
elif [ $TARGET == "C21" ] 
then
    TARGET_FILE="SOMANET-C21-DX_G2.xn"
else
    echo "Wrong target"
    echo "Use 'C22' or 'C21'"
    exit 1
fi


SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

echo "Delete target: " $TARGET

# Erase chip
xflash --erase-all --target-file $SCRIPTPATH/$TARGET_PATH/$TARGET_FILE
echo "done...exit"
