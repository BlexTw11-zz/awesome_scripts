#!/bin/bash
################################################
# Erase your CORE module with this nice script #
################################################

TARGET="SOMANET-C22.xn"
TARGET_PATH="targets"

SCRIPT=$(readlink -f "$0")
SCRIPTPATH=$(dirname "$SCRIPT")

echo "Delete target: " $TARGET

# Erase chip
xflash --erase-all --target-file $SCRIPTPATH/$TARGET_PATH/$TARGET
