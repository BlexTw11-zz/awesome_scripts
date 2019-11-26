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


class ExceptionNoBinary(Exception):
    pass


class ExceptionLRZSZMissing(Exception):
    pass


class UARTFWUploader(object):

    def __init__(self, serial, binary_path=None, baudrate=115200):
        self.__binary_path = None
        if binary_path:
            self.__binary_path = self._test_test_path(binary_path)

        self._test_lrzsz_installation()
       
        self.__port = '' 
        if '/dev/' not in serial:
            self.__port = '/dev/'
        self.__modem_write = 'sb'
        self.__modem_read = 'rb'
        self.__port += serial
        self.__baudrate = baudrate

    @staticmethod
    def _test_test_path(path):
        if os.path.isfile(path):
            return path
        raise ExceptionNoBinary("No file found")

    @staticmethod
    def _test_lrzsz_installation():
        if sp.call('command -v sb', shell=True, stdout=sp.DEVNULL) != 0:
            raise ExceptionLRZSZMissing("lrzsz not installed!")

    @staticmethod
    def _print(res):
        if not res:
            return
        try:
            res = res.decode(errors='backslashreplace')
            if len(res) > 0:
                for l in res.splitlines():
                    print('>>> ' + l)
            else:
                print('-')
        except UnicodeDecodeError:
            print('Error')
            print(res)

    def forward_to_serial(self, ser, proc):
        MAX_READ_SIZE = 4096
        while True:
            try:
                data = proc.stdout.read1(MAX_READ_SIZE)
            except IOError as e:
                if e.errno == errno.EPIPE:
                    break

            if not data:
                break  # EOF
            ser.write(data)

    def forward_to_app(self, ser, proc):
        while True:
            try:
                if ser.in_waiting:
                    msg = ser.read()
                    proc.stdin.write(msg)
                    proc.stdin.flush()
            except IOError as e:
                if e.errno == errno.EPIPE:
                    break

    def _call(self, args, uart):
        proc = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE)

        fwc = threading.Thread(target=self.forward_to_app, args=(uart,proc,))
        fwc.start()

        self.forward_to_serial(uart, proc)

        fwc.join()

    def _send_cmd(self, cmd, timeout=2):
        uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        uart.reset_input_buffer()
        _cmd = cmd

        for c in _cmd: 
            uart.write(c.encode())
            time.sleep(0.002)
        uart.write(b'\r\n')

        # wait for reply
        t0 = time.time()
        while uart.in_waiting == 0:
            if (time.time() - t0) > timeout:
                print("Timeout! Not receiving reply!")
                return None
        _input_bytes = uart.in_waiting

        if _input_bytes == 0:
            return b''
        _input = uart.read(_input_bytes)
        uart.reset_input_buffer()
        uart.close()
        return _input

    def __write_file(self, cmd, file_path):
        file_size = os.path.getsize(file_path)
        # Speed: roughly 8000 bytes/seconds
        timeout = (file_size / 8000) + 1

        if timeout < 5:
            timeout = 5

        res = self._send_cmd('\n')
        if not res:
            return

        res = self._send_cmd(cmd)
        if not res:
            return

        self._print(res)
        print()

        uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        self._call([self.__modem_write, file_path], uart)
        time.sleep(0.01)

        res = uart.read(uart.in_waiting)
        uart.close()
        return res

    def __read_file(self, cmd, args):
        file_path = args.read
        file_size = self.read_file_size(file_path)
        if not file_size:
            print('Error! Just try again')
            return

        timeout = (file_size / 8000) + 1
        if timeout < 5:
            timeout = 5

        self._send_cmd('\n')
        cmd += ' '+file_path
        res = self._send_cmd(cmd)
        self._print(res)

        print()
        uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        modem = [self.__modem_read, '-E', '-t', str(timeout*10)]

        self._call(modem, uart)
        time.sleep(0.01)

        if uart.in_waiting > 0:
            res = uart.read(uart.in_waiting)
        uart.close()

        return res

    def read_file_size(self, _file):
        retry = 5
        while True:
            res = self.send_cmd('getlist')
            res = res.decode(errors='backslashreplace')
            re_res = re.search(r'%s, size: (\d+)' % _file, res)
            if re_res:
                return int(re_res.group(1))

            if retry == 0:
                return
            retry += 1

    def send_cmd(self, cmd):
        retry = 5
        while True:
            res = self._send_cmd(cmd)
            if b'Unknown command' not in res or retry == 0:
                break
            retry -= 1
        return res

    def get_list(self):
        return self.send_cmd('getlist')

    def get_info(self):
        return self.send_cmd('info')

    def check(self):
        return self.send_cmd('check')

    def boot(self):
        return self._send_cmd('boot')

    def remove(self, file_name):
        return self._send_cmd('remove %s' % file_name)

    def flash_fw(self, binary_path=None):
        if not binary_path:
            binary_path = self.__binary_path

        if not re.match(r'^app.+\.bin$', binary_path, re.M):
            raise ExceptionNoBinary('Error! "%s" is not a valid binary name. Needs to be "app_*.bin"')

        return self.__write_file('flash', binary_path)

    def write_file(self, file_path):
        return self.__write_file('write', file_path)

    def read_file(self, file_path):
        return self.__read_file('read', file_path)

    def remove_bin(self):
        bin_empty = 'app_empty.bin'
        if not os.path.isfile(bin_empty):
            with open(bin_empty, 'w') as f:
                f.write("void\n")
        return self.__write_file('flash', bin_empty)


def _check_result(res):
    UARTFWUploader._print(res)
    if not res:
        print("...FAILED!")


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', dest='app', metavar='FILE', help='flash "FILE" to device', type=str)
    parser.add_argument('-w', dest='write', metavar='FILE', help='write "FILE" to device', type=str)
    parser.add_argument('-r', dest='read', metavar='FILE', help='read "FILE" on device', type=str)
    parser.add_argument('-d', dest='device', help='serial device', type=str, default='ttl232r-3v3-0')
    parser.add_argument('-b', dest='boot', help='boot device', action='store_true')
    parser.add_argument('-l', dest='getlist', help='get file list', action='store_true')
    parser.add_argument('-i', dest='info', help='get flash storage info', action='store_true')
    parser.add_argument('-c', dest='check', help='Check the flash storage', action='store_true')
    parser.add_argument('-rm', dest='remove', metavar='FILE', help='remove "FILE" from device', type=str)
    parser.add_argument('-rmb', dest='remove_bin', help='remove app from device', action='store_true')

    args = parser.parse_args()
    dev = args.device
    uart_fw = UARTFWUploader(dev)
    if args.app:
        print('Flash FW...')
        res = uart_fw.flash_fw(args.app)
        _check_result(res)
    elif args.write:
        print('Write file...')
        res = uart_fw.write_file(args.write)
        _check_result(res)
    elif args.read:
        print('read file...')
        res = uart_fw.read_file(args)
        _check_result(res)
    elif args.boot:
        print('Boot device...')
        res = uart_fw.boot()
        _check_result(res)
    elif args.getlist:
        print('Get List...')
        res = uart_fw.get_list()
        _check_result(res)
    elif args.check:
        print('Check flash storage...')
        uart_fw.check()
    elif args.info:
        print('Get info...')
        res = uart_fw.get_info()
        _check_result(res)
    elif args.remove:
        print('Remove "%s" from device...' % args.remove)
        uart_fw.remove(args.remove)
    elif args.remove_bin:
        print("Remove app from device...")
        uart_fw.remove_bin()
    else:
        parser.print_help()


