#!/usr/bin/python3

import subprocess as sp
import os
import sys
import serial
import time
import re
import struct
import threading
import errno
#from modem import YMODEM
import modem


uart = None
def getc(size, timeout=5, debug=None):
    return uart.read(size) or None


def putc(data, timeout=5, debug=None):
    return uart.write(data)


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
       
        self.__port = '' 
        if '/dev/' not in serial:
            self.__port = '/dev/'
        self.__port += serial
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

    def _print(self, res):
        try:
            res = res.decode(errors='backslashreplace')
            if len(res) > 0:
                for l in res.splitlines():
                    print('>>> ' + l)
            else:
                print('-')
        except UnicodeDecodeError:
            print(res)



    def _send_cmd(self, cmd):
        uart = serial.Serial(self.__port, self.__baudrate, timeout=3)
        uart.reset_input_buffer()
        _cmd = cmd
        for c in _cmd: 
            uart.write(c.encode())
            time.sleep(0.002)
        uart.write(b'\r\n')
        time.sleep(0.05)
        _input_bytes = uart.in_waiting
        if _input_bytes == 0:
            return b''
        _input = uart.read(_input_bytes)
        uart.reset_input_buffer()
        uart.close()
        return _input

    def get_list(self):
        res = self._send_cmd('getlist')
        self._print(res)
        return res != ''

    def get_info(self):
        res = self._send_cmd('info')
        self._print(res)
        return res != ''

    def boot(self):
        res = self._send_cmd('boot')
        self._print(res)
        return res != ''

    def remove(self, file_name):
        res = self._send_cmd('remove %s' % file_name)
        self._print(res)
        return res != ''

    def __write_file(self, cmd, file_path):
        global uart
        file_size = os.path.getsize(file_path)
        # Speed: roughly 8000 bytes/seconds
        self.__timeout = (file_size / 8000) + 1
        if self.__timeout < 5:
            self.__timeout = 5
        self._send_cmd('\n')
        res = self._send_cmd(cmd)
        self._print(res)
        print()
        #:wtime.sleep(0.5)
        uart = serial.Serial(self.__port, self.__baudrate, timeout=3)

        ymodem = modem.YMODEM(getc, putc)
        ymodem.send(file_path)


        #input('wait')
        #self._call('stty -F %s %d' % (self.__port, self.__baudrate))
        #self._call('%s %s -k  > %s < %s' % (self.__modem, file_path, self.__port, self.__port))
        #self._call([self.__modem, file_path], uart)
        #sp.run('%s %s -k' % (self.__modem, file_path), stdout=self.__port, stdin=self.__port)
        #ymodem(uart, file_path)
        time.sleep(0.01)
        res = uart.read(uart.in_waiting)
        print()
        self._print(res)
        uart.close()
        return res

    def flash_fw(self, binary_path=None):
        if not binary_path:
            binary_path = self.__binary_path
        if not re.match(r'^app.+\.bin$', binary_path, re.M):
            raise ExceptionNoBinary('Error! "%s" is not a valid binary name. Needs to be "app_*.bin"')
        return self.__write_file('flash', binary_path) != ''

    def write_file(self, file_path):
        return self.__write_file('write', file_path) != ''

def _check_result(res):
    if not res:
        print("...FAILED!", res)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='flash', help='flash "PATH" to device', type=str)
    parser.add_argument('-w', dest='write', help='write "PATH" to device', type=str)
    parser.add_argument('-d', dest='device', help='serial device', type=str, default='ttl232r-3v3-0')
    parser.add_argument('-b', dest='boot', help='boot device', action='store_true')
    parser.add_argument('-l', dest='getlist', help='get file list', action='store_true')
    parser.add_argument('-i', dest='info', help='get flash storage info', action='store_true')
    parser.add_argument('-r', dest='remove', help='remove "FILE" from device', type=str)
    args = parser.parse_args()
    dev = args.device
    uart_fw = UARTFWUploader(dev)
    if args.flash:
        print('Flash FW...')
        res = uart_fw.flash_fw(args.flash)
        _check_result(res)
    elif args.write:
        print('Write file...')
        res = uart_fw.write_file(args.write)
        _check_result(res)
    elif args.boot:
        print('Boot device...')
        res = uart_fw.boot()
        _check_result(res)
    elif args.getlist:
        print('Get List...')
        res = uart_fw.get_list()
        _check_result(res)
    elif args.info:
        print('Get info...')
        res = uart_fw.get_info()
        _check_result(res)
    elif args.remove:
        print('Remove "%s" from device...' % args.remove)
        uart_fw.remove(args.remove)
    else:
        parser.print_help()


