#!/usr/bin/python3

import subprocess as sp
import os
import sys
import serial
import time

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
        if len(res) > 0:
            for l in res.splitlines():
                print('>>> ' + l)

    def _call(self, args):
        return sp.call(args, stdout=sp.DEVNULL, stderr=sp.DEVNULL, shell=True, timeout=self.__timeout)

    def _send_cmd(self, cmd):
        uart = serial.Serial(self.__port, self.__baudrate, timeout=3)
        uart.reset_input_buffer()
        _cmd = cmd
        for c in _cmd: 
            uart.write(c.encode())
            time.sleep(0.001)
        uart.write(b'\r\n')
        time.sleep(0.05)
        _input_bytes = uart.in_waiting
        if _input_bytes == 0:
            return ''
        _input = uart.read(_input_bytes)
        uart.reset_input_buffer()
        uart.close()
        return _input.decode()

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
        return 'booting' in res

    def flash(self, binary_path=None):
        file_size = os.path.getsize(binary_path)
        self.__timeout = (file_size / 1024) + 1
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
        res = self._call('%s %s > %s < %s' % (self.__modem, self.__binary_path, self.__port, self.__port))
        if res:
            return 3
        return 0


def _check_result(res):
    if not res:
        print("...FAILED!", res)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', dest='flash', help='flash PATH to device', type=str)
    parser.add_argument('-d', dest='device', help='serial device', type=str, default='ttl232r-3v3-0')
    parser.add_argument('-b', dest='boot', help='boot device', action='store_true')
    parser.add_argument('-l', dest='getlist', help='get file list', action='store_true')
    parser.add_argument('-i', dest='info', help='get flash storage info', action='store_true')
    args = parser.parse_args()
    dev = args.device
    if args.flash:
        print('Flash FW...')
        uart_fw = UARTFWUploader(dev, args.flash)
        res = uart_fw.flash()
        _check_result(res == 0)
    elif args.boot:
        print('Boot device...')
        uart_fw = UARTFWUploader(dev)
        res = uart_fw.boot()
        _check_result(res)
    elif args.getlist:
        print('Get List...')
        uart_fw = UARTFWUploader(dev)
        res = uart_fw.get_list()
        _check_result(res)
    elif args.info:
        print('Get info...')
        uart_fw = UARTFWUploader(dev)
        res = uart_fw.get_info()
        _check_result(res)
    else:
        parser.print_help()


