#!/usr/bin/env python
#####################################################################
# Init your fresh cloned workspace. This script will automatically  # 
# write your bsp-file in all main.xc files and set the right target #
# in Makefile.                                                      #
#####################################################################


import os
import sys
import re
import argparse

com_dict = {
    'ecat': 'ComEtherCAT-rev-a.bsp',
    'enet': 'ComEthernet-rev-a.bsp',
    'serial': 'ComSerial-rev-a.bsp',
}

core_dict = {
    'c21': 'CoreC21.bsp',
    'c21b': 'CoreC21-rev-b.bsp',
    'c22': 'CoreC22.bsp',
    'c2x': 'CoreC2X.bsp',
}


drive_dict = {
    
    'd100a': 'Drive100.bsp',

    'd1000c4': 'Drive1000-rev-c4.bsp',
    'd1000d1': 'Drive1000-rev-d1.bsp',

    'd50duo': 'Drive50Duo-rev-a.bsp',

    'd500': 'Drive500-rev-a1.bsp',
    'd5000a3': 'Drive5000-rev-a3.bsp',
}

target_dict = {
    'c22': 'SOMANET-CoreC22',
    'c21': 'SOMANET-CoreC21',
    'c21b': 'SOMANET-CoreC21-rev-b',
    'c2x':  'SOMANET-CoreC2X',
}


arg_parser = argparse.ArgumentParser(description='Synapticon SOMANET workspace initializer')
arg_parser.add_argument('-p', '--path', help='Path to repository', dest='path')
arg_parser.add_argument('-com', default='', help='COM module BSP', dest='com')
arg_parser.add_argument('-core', default='c22a', help='CORE module BSP', dest='core')
arg_parser.add_argument('-drive', default='', help='IFM module BSP', dest='drive')

args = arg_parser.parse_args()


path = args.path
com_bsp = args.com
core_bsp = args.core
drive_bsp = args.drive

err = False
if not com_bsp in com_dict and com_bsp: 
    print 'Wrong COM module'
    print com_dict
    err = True
if not core_bsp in core_dict and core_bsp:
    print 'Wrong CORE module'
    print core_dict
    err = True
if not drive_bsp in drive_dict and drive_bsp:
    print 'Wrong IFM module'
    print drive_dict
    err = True
if not drive_bsp:
    print 'No IFM module'
    err = True

if not core_bsp in target_dict:
    print 'Wrong target'
    print core_bsp
    err = True

if err:
    arg_parser.print_help()
    sys.exit(1)

re_com = re.compile(r'\#include.+\<COM_.+\>')
re_core = re.compile(r'\#include.+\<CORE_.+\>')
re_drive = re.compile(r'\#include.+\<DRIVE_.+\>')
re_target = re.compile(r'TARGET = ?(SOMANET-CoreC22|SOMANET-CoreC21|SOMANET-CoreC21-rev-b|SOMANET-CoreC2X|)\n')

for root, dirs, files in os.walk(path):
    for name in files:
        if re.search(r'app_', root): 
            if name == 'main.xc':
                file_name = os.path.join(root, name)
                print file_name
                f = open(file_name, 'r')
                
                f_txt = f.read()
                f.close()
                if core_bsp:
                    f_txt = re_core.sub('#include <'+core_dict[core_bsp]+'>', f_txt)
                    print 'Core', core_bsp

                if drive_bsp:
                    f_txt = re_drive.sub('#include <'+drive_dict[drive_bsp]+'>', f_txt)
                    print 'Drive', drive_bsp

                if com_bsp:
                    com_found = re_com.search(f_txt)
                    if com_found:
                        f_txt = re_com.sub('#include <'+com_dict[com_bsp]+'>', f_txt)
                        print 'Replace Com', com_bsp
                    else:
                        #f = open(file_name, 'r')
                        #f_txt = f.readlines()
                        # Insert COM bsp above found CORE bsp
                        for i in range(len(f_txt)):
                            if re_core.search(f_txt[i]):
                                f_txt.insert(i, '#include <'+com_dict[com_bsp]+'>\n')
                                print 'Insert Com', com_bsp
                                break
                        f_txt = ''.join(f_txt)


                f = open(file_name, 'w')
                if not f:
                    print 'Error: Could not open file to write'
                    sys.exit(1)

                f.write(f_txt)
                f.close()

            if name == 'Makefile':
                f = open(os.path.join(root, name), 'r')
                f_txt = f.read()
                f.close()
                target_found = re_target.search(f_txt)

                if target_found:
                    f_txt = re_target.sub('TARGET = %s\n' % target_dict[core_bsp], f_txt)
                    print 'Insert Target', target_dict[core_bsp]
                    f = open(os.path.join(root, name), 'w')
                    f.write(f_txt)
                    f.close()



