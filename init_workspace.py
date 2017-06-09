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
    'ecat': 'COM_ECAT-rev-a.bsp',
    'enet': 'COM_ETHERNET-rev-a.bsp',
    'serial': 'COM_SERIAL-rev-a.bsp',
}

core_dict = {
    'c21a': 'CORE_C21-rev-a.bsp',
    'c21b': 'CORE_C21-rev-b.bsp',
    'c21g2': 'CORE_C21-DX_G2.bsp',

    'c22a': 'CORE_C22-rev-a.bsp',    
}


ifm_dict = {
    
    'dc100a': 'IFM_DC100-rev-a.bsp',
    'dc100b': 'IFM_DC100-rev-b.bsp',

    'dc1kc1': 'IFM_DC1K-rev-c1.bsp',
    'dc1kc2': 'IFM_DC1K-rev-c2.bsp',
    'dc1kc3': 'IFM_DC1K-rev-c3.bsp',
    'dc1kc4': 'IFM_DC1K-rev-c4.bsp',

    'dc30a': 'IFM_DC30-rev-a.bsp',

    'dc300a': 'IFM_DC300-rev-a.bsp',

    'dc500a': 'IFM_DC500-rev-a1.bsp',
    'dc5ka3': 'IFM_DC5K-rev-A3.bsp',
}

target_dict = {
    'c22': 'SOMANET-C22',
    'c21': 'SOMANET-C21-DX',
    'c21g2': 'SOMANET-C21-DX_G2',
}


arg_parser = argparse.ArgumentParser(description='Synapticon SOMANET workspace initializer')
arg_parser.add_argument('-p', '--path', help='Path to repository', dest='path')
arg_parser.add_argument('-com', default='', help='COM module BSP', dest='com')
arg_parser.add_argument('-core', default='c22a', help='CORE module BSP', dest='core')
arg_parser.add_argument('-ifm', default='', help='IFM module BSP', dest='ifm')

args = arg_parser.parse_args()


path = args.path
com_bsp = args.com
core_bsp = args.core
ifm_bsp = args.ifm

err = False
if not com_bsp in com_dict and com_bsp: 
    print 'Wrong COM module'
    err = True
if not core_bsp in core_dict and core_bsp:
    print 'Wrong CORE module'
    err = True
if not ifm_bsp in ifm_dict and ifm_bsp:
    print 'Wrong IFM module'
    err = True
if not ifm_bsp:
    print 'No IFM module'
    err = True
if err:
    arg_parser.print_help()
    sys.exit(1)

if core_bsp == 'c22a':
    target = 'SOMANET-C22'
elif core_bsp == 'c21a' or core_bsp == 'c21b':
    target = 'SOMANET-C21-DX'
elif core_bsp == 'c21g2':
    target = 'SOMANET-C21-DX_G2'

re_com = re.compile(r'\#include.+\<COM_.+\>')
re_core = re.compile(r'\#include.+\<CORE_.+\>')
re_ifm = re.compile(r'\#include.+\<IFM_.+\>')
re_target = re.compile(r'TARGET = *\n')

for root, dirs, files in os.walk(path):
    for name in files:
        if name == 'main.xc':
            file_name = os.path.join(root, name)
            print file_name
            f = open(file_name, 'r')
            
            f_txt = f.read()
            f.close()
            if core_bsp:
                f_txt = re_core.sub('#include <'+core_dict[core_bsp]+'>', f_txt)
                print 'CORE', core_bsp

            if ifm_bsp:
                f_txt = re_ifm.sub('#include <'+ifm_dict[ifm_bsp]+'>', f_txt)
                print 'IFM', ifm_bsp

            if com_bsp:
                com_found = re_com.search(f_txt)
                if com_found:
                    f_txt = re_com.sub('#include <'+com_dict[com_bsp]+'>', f_txt)
		    print 'Replace COM', com_bsp
                else:
                    #f = open(file_name, 'r')
                    #f_txt = f.readlines()
                    # Insert COM bsp above found CORE bsp
                    for i in range(len(f_txt)):
                        if re_core.search(f_txt[i]):
                            f_txt.insert(i, '#include <'+com_dict[com_bsp]+'>\n')
                    	    print 'Insert COM', com_bsp
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
            f_txt = re_target.sub('TARGET = %s\n' % target, f_txt)
            f = open(os.path.join(root, name), 'w')
            f.write(f_txt)
            f.close()



