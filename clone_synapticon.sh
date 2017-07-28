#!/bin/bash

GIT_CMD="git clone"
SYN_REPO_URL=https://github.com/synapticon/
SYN_REPO_MOTOR=sc_sncn_motorcontrol
SYN_REPO_ECAT=sc_sncn_ethercat
SYN_REPO_ECAT_DRIVE=sc_sncn_ethercat_drive
SYN_REPO_BASE=sc_somanet-base

${GIT_CMD} $SYN_REPO_URL$SYN_REPO_MOTOR
${GIT_CMD} $SYN_REPO_URL$SYN_REPO_ECAT
${GIT_CMD} $SYN_REPO_URL$SYN_REPO_ECAT_DRIVE
${GIT_CMD} $SYN_REPO_URL$SYN_REPO_BASE
