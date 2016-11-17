#####################################################################
# Init your fresh cloned workspace. This script will automatically 
# write your bsp-file in all main.xc files and set the right target
# in Makefile.
####################################################################


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
    'c21a': 'CORE_C22-rev-a.bsp',
    'c21b': 'CORE_C22-rev-b.bsp',

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

    'dc500a': 'IFM_DC300-rev-a1.bsp',
    'dc5ka3': 'IFM_DC300-rev-A3.bsp',
}

target_dict = {
    'c22': 'SOMANET-C22',
    'c21': 'SOMANET-C21-DX',
}

arg_parser = argparse.ArgumentParser(description='Synapticon SOMANET workspace initializer')
arg_parser.add_argument('-com', default='', help='COM module', dest='com')
arg_parser.add_argument('-core', default='c22a', help='CORE module', dest='core')
arg_parser.add_argument('-ifm', default='', help='IFM module', dest='ifm')

args = arg_parser.parse_args()

com_bsp = args.com
core_bsp = args.core
ifm_bsp = args.ifm

err = False
if not com_bsp in com_dict: 
    print 'Wrong COM module'
    err = True
if not core_bsp in core_dict:
    print 'Wrong CORE module'
    err = True
if not ifm_bsp in ifm_dict:
    print 'Wrong IFM module'
    err = True
if err:
    sys.exit(1)

if core_bsp == 'c22a':
    target = 'SOMANET-C22'
else:
    target = 'SOMANET-C21-DX'

re_com = re.compile(r'COM_BOARD_REQUIRED')
re_core = re.compile(r'CORE_BOARD_REQUIRED')
re_ifm = re.compile(r'IFM_BOARD_REQUIRED')
re_target = re.compile(r'TARGET = ')

for root, dirs, files in os.walk(sys.argv[1]):
    for name in files:
        if name == 'main.xc':
            f = open(os.path.join(root, name), 'r')
            f_txt = f.read()
            f.close
            f_txt = re_core.sub(core_dict[core_bsp], f_txt)
            f_txt = re_ifm.sub(ifm_dict[ifm_bsp], f_txt)
            f_txt = re_com.sub(com_dict[com_bsp], f_txt)
            f = open(os.path.join(root, name), 'w')
            f.write(f_txt)
            f.close()

        if name == 'Makefile':
            f = open(os.path.join(root, name), 'r')
            f_txt = f.read()
            f.close
            f_txt = re_target.sub('TARGET = ' + target, f_txt)
            f = open(os.path.join(root, name), 'w')
            f.write(f_txt)
            f.close()
