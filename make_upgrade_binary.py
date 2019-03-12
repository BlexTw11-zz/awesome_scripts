#!/usr/bin/python3

import argparse
import subprocess as sp
import datetime
import re
import os

XTIMECOMPOSER_VERSION="14.3"
XFLASH_CMD="xflash --noinq --factory-version " + XTIMECOMPOSER_VERSION + " --upgrade 1 %s -o %s"

arg_parser = argparse.ArgumentParser(description='Build upgrade binary')
arg_parser.add_argument('path', type=str, help="Path to .xe file")
arg_parser.add_argument('-t', required=False, action='store_true', help='Binary name with timestamp')
arg_parser.add_argument('-v', type=str, help='Add additional informations to binary name (e.g. version, fix,....)')

args = arg_parser.parse_args()

re_name = re.compile(r'/?(.+?).xe$')

binary_name = re_name.search(args.path).group(1)
if args.v:
    binary_name += '-'+args.v

if args.t:
    timestamp = datetime.datetime.today().strftime('%y%m%d-%H%M%S')
    binary_name += '-'+timestamp

binary_name += '.bin'
print('Name', binary_name)

#sp.call((XFLASH_CMD % (args.path, binary_name)).split(' '))

print(os.listdir())
