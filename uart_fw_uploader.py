#!/usr/bin/python3

import subprocess as sp
import os
import sys
import serial


class ExceptionNoBinary(Exception):
    pass


class ExceptionLRZSZMissing(Exception):
    pass


class UARTFWUploader(object):

    def __init__(self, serial, binary_path=None, baudrate=115200, modem='y'):
        self.__binary_path = None
        if binary_path:
            self.__binary_path = self._test_binary_path(binary_path)
        self._test_lrzsz_installation()
        self.__port = '/dev/%s' % serial
        if modem == 'x':
            self.__modem = 'sx'
        elif modem == 'y':
            self.__modem = 'sb'
        elif modem == 'z':
            self.__modem = 'sz'
        self.__baudrate = baudrate

    @staticmethod
    def _test_binary_path(path):
        if os.path.isfile(path):
            return path
        raise ExceptionNoBinary("No binary found")

    @staticmethod
    def _test_lrzsz_installation():
        if sp.call('command -v sb', shell=True, stdout=sp.DEVNULL) != 0:
            raise ExceptionLRZSZMissing("lrzsz not installed!")

    @staticmethod
    def _call(args):
        return sp.call(args, stdout=sp.DEVNULL, stderr=sp.DEVNULL, shell=True, timeout=10)

    def boot(self):
        uart = serial.Serial(self.__port, self.__baudrate, timeout=3)
        uart.reset_input_buffer()
        uart.write(b'boot\n')
        _input = uart.read(14)
        uart.reset_input_buffer()
        uart.close()
        return b'booting' in _input

    def flash(self, binary_path=None):
        uart = serial.Serial(self.__port, self.__baudrate, timeout=3)
        uart.reset_input_buffer()
        uart.close()
        if binary_path:
            self.__binary_path = self._test_binary_path(binary_path)
        res = self._call('stty -F %s %d' % (self.__port, self.__baudrate))
        if res:
            print('Setting up %s FAILED' % self.__port, file=sys.stderr)
            return 1
        res = self._call('echo "flash" > %s' % self.__port)
        if res:
            print('Sending cmd FLASH to %s FAILED' % self.__port, file=sys.stderr)
            return 2
        print("Flash...")
        res = self._call('%s %s > %s < %s' % (self.__modem, self.__binary_path, self.__port, self.__port))
        if res:
            return 3
        return 0


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument(dest='flash', help='flash PATH to device', type=str)
    parser.add_argument('-d', dest='device', help='serial device', type=str, default='ttl232r-3v3')
    parser.add_argument('-b', dest='boot', help='boot device', action='store_true')
    args = parser.parse_args()
    dev = args.device
    if args.flash:
        uart_fw = UARTFWUploader(dev, args.flash)
        res = uart_fw.flash()
        if res:
            print("...FAILED!", res)
        else:
            print("...done", res)
    elif args.boot:
        uart_fw = UARTFWUploader(dev)
        res = uart_fw.boot()
        if res == 0:
            print("...done")
        else:
            print("...FAILED!", res)
    else:
        parser.print_help()   
