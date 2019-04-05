#!/bin/bash

ECAT="/opt/etherlab/bin/ethercat"
MASTERINDEX=0
NODEINDEX=""
OPTSTRING="hn:a"

#
# Helper Functions
#

printusage ()
{
    echo "Usage: $( basename $0 ) [-h] [-a | -n <nodeid>] [--]  <filename>"
    echo
    echo "  -h        print this nice help"
    echo "  -n <id>   update only node <id> (id = { 0, 1, ... , N }) (default is 0)"
    echo "  -m <id>   select master to use"
    echo "  -a        update all nodes of type CiA402"
    echo "<filename>  full path of the firmware to write to the node(s)"
}

# Update a single node
#
# Put node into boot mode and check if the boot stete is reached
# Setting the boot mode has to be done two times to confirm the BOOT state
# after the bootmanager is loaded.
update_node ()
{
    INDEX=$@
    shift $@

    # The first time the slaves receives the BOOT state command it will reboot und result in
    # INIT + E state because no valid firmware is present.

    ${ECAT} states -p ${INDEX} BOOT
    #NODESTATE=$( ${ECAT} slaves -p ${INDEX} | cut -d ' ' -f 5 )
    NODESTATE=""

    timeoutcounter=10

    while [ -z "${NODESTATE}" ]
    do
        (( timeoutcounter-- ))
        if (( timeoutcounter <= 0 ))
        then
            echo -e "\nError: timeout waiting for node to reach first stage"
            return 1
        fi

        echo -n ":"
        sleep 1
        NODESTATE=$( ${ECAT} -m ${MASTERINDEX} slaves -p ${INDEX} | cut -d ' ' -f 5 )
    done

    if [ x"${NODESTATE}" != x"INIT" -a x"${NODESTATE}" != x"BOOT" ]
    then
        echo "[ERROR] failed to get pre-boot mode!"
        return 1
    fi

    # We have to wait for a while to let the EtherCAT master realize what happend
    # on the bus before we can finally switch to the BOOT state to prepare the file
    # transfer.

    timeoutcounter=20

    # second time of BOOT set.
    #NODESTATE=$( ${ECAT} slaves -p ${INDEX} | grep -e "^${INDEX}" | cut -d ' ' -f 5 )
    NODESTATE=""

    while [ x"${NODESTATE}" != x"BOOT" ]
    do
        (( timeoutcounter-- ))
        if (( timeoutcounter <= 0 ))
        then
            echo -e "\nError: timeout waiting for node to reach second stage"
            return 1
        fi

        echo -n "."
        ${ECAT} states -p ${INDEX} BOOT
        sleep 1
        NODESTATE=$( ${ECAT} -m ${MASTERINDEX} slaves -p ${INDEX} | cut -d ' ' -f 5 )
    done

    # transfer the binary
    ${ECAT} -m ${MASTERINDEX} foe_write -p ${INDEX} ${FILENAME}
    ecaterr=$?
    if [ ${ecaterr} -ne 0 ]
    then
        echo "Error transfer new firmware!"
        return ${ecaterr}
    fi

    echo "Firmware transfer complete"

    return 0
}

# Mltinode Update
update_cia_slaves()
{
    ret=0
    ALL_IDX=$( ${ECAT} -m ${MASTERINDEX} slaves | awk '/CiA402 Drive/ { printf "%d ", $1 ; }' )

    if [ -z ${ALL_IDX} ]
    then
        echo "Warning no CiA402 slave found, please check your network"
        return 1
    fi

    for idx in ${ALL_IDX}
    do
        update_node ${idx}
        if [ $? -ne 0 ]
        then
            echo "*** Error updating node ${idx}"
            ret=1
        fi
    done

    return ${ret}
}


#
# Main
#

if [ ! -e ${ECAT} ]
then
    ECAT=`which ethercat`

    if [ -z ${ECAT} ]
    then
        echo "Error Ethercat command not found\n"
        exit 1
    fi
fi

# check version of ecat
ECAT_VERSION=( $( ${ECAT} version | cut -s -f 4 -d ' ' | cut -s -d '-' -f 1-3 --output-delimiter=" " ) )

# check for base version validity
if [ x"${ECAT_VERSION}" != x"1.5.2" ]
then
    echo "Unsupported version. Exit."
    exit 1
fi

# now check if the right synapticon version is used
if [ -z ${ECAT_VERSION[1]} ] || [ ${ECAT_VERSION[1]} != "sncn" ]
then
    echo "Unsupported version. No sncn patch applied. Exit."
    exit 1
fi

if [ -z ${ECAT_VERSION[2]} ] || (( ${ECAT_VERSION[2]} < 2 ))
then
    echo "Unsupported version, sncn patch level too small"
    exit 1
fi

while getopts ${OPTSTRING} arg
do
    case "$arg" in
    h)
        printusage $0
        #echo "Usage: $0 [-h] [-n <nodeid>] [--]  <filename>"
        exit 0
        ;;

    n)
        if [ ! -z ${NODEINDEX} ]
        then
            echo "Error, only single or multinode update possible"
            printusage $0
            exit 1
        fi
        NODEINDEX=${OPTARG}
        ;;

    m)
        # FIXME add master ranges like the `ethercat` command provides
        MASTERINDEX=${OPTARG}
        ;;

    a)
        if [ ! -z ${NODEINDEX} ]
        then
            echo "Error, only single or multinode update possible"
            printusage $0
            exit 1
        fi
        NODEINDEX=-1
        ;;

    *)
        echo "Unknown option ${arg}"
        exit 1
        ;;
    esac
done

if (( $OPTIND > $# ))
then
    echo "Error filename is missing"
    exit 1
fi

if (( $OPTIND < $# ))
then
    echo "Error too much filenames"
    exit 1
fi

args=("$@")
FILENAME=${args[$OPTIND-1]}

if [ ! -e ${FILENAME} ]
then
    echo "Error '${FILENAME}' does not exist - please check the file path"
    exit 1
fi

#
# Start the update
#

### DEBUG ###
#NODESTATE=$( ${ECAT} slaves -p ${NODEINDEX} | grep -e "^${NODEINDEX}" | cut -d ' ' -f 5 )
#echo ${NODESTATE}

if [ -z ${NODEINDEX} ]
then
    NODEINDEX=0
fi

if [ ${NODEINDEX} -ne -1 ]
then
    update_node ${NODEINDEX}
    exit $?
else
    update_cia_slaves
    exit $?
fi

