#!/usr/bin/python3

"""
    SOMANET UART Firmware Uploader v1.0
    author: Henrik Strötgen
"""

import sys
import subprocess as sp
import os
import serial
import time
import re
import threading
import errno
import zipfile
import tempfile
import glob
import logging

from ymodem.YModem import YModem

# logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='[%(levelname)s]: %(message)s')
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ExceptionUART(Exception):
    pass


class ExceptionNoBinary(ExceptionUART):
    pass


class ExceptionLRZSZMissing(ExceptionUART):
    pass


class UARTFWUploader:

    def __init__(self, serial, binary_path=None, baudrate=115200):
        """
        UART Firmware Uploader.
        :param serial: path to serial device (e.g. ttyUSB0 or /dev/ttyUSB0)
        :type serial: str
        :param binary_path: Optional path to binary file
        :type binary_path: str
        :param baudrate: Baud rate of serial device. Bootlaoder has 115200. So don't change it!
        :type baudrate: int
        """
        self.__binary_path = None
        if binary_path:
            self.__binary_path = self._test_path(binary_path)

        if not serial.startswith('/dev/'):
            self.__port = os.path.join('/dev/', serial)
        else:
            self.__port = serial

        if not os.path.exists(self.__port):
            raise ExceptionUART(f"Device \"{self.__port}\" does not exists")

        self.__baudrate = baudrate

        self.modem = YModem(self.getc, self.putc)

    @staticmethod
    def _test_path(path):
        """
        Check, if a file, which is to be sent, is existing.
        If not, ExceptionNoBinary is raised.
        :param path: Path to file
        :type path: str
        :return: Path to file
        :rtype: str
        """
        if os.path.isfile(path):
            return path
        raise ExceptionNoBinary("No file found")

    @staticmethod
    def _print(res):
        """
        Print a received message in a console style format.
        :param res: Incoming message
        :type res: binary
        """
        if not res:
            return
        try:
            res = res.decode(errors='backslashreplace')

            if len(res) > 0:
                for l in res.splitlines():
                    if l:
                        l = "".join([r for r in l if r.isprintable()])
                        logger.info(f'>>> {l}')
            else:
                logger.info('-')
        except UnicodeDecodeError:
            logger.error(f'Error: {res}')

    def getc(self, size):
        return self.uart.read(size) or None

    def putc(self, data):
        return self.uart.write(data)

    def _send_cmd(self, cmd, timeout=2):
        """
        Send a single command to bootloader. NOT YMODEM related.
        :param cmd: Command (like getlist, boot, flash)
        :type cmd: str
        :param timeout: Timeout in seconds
        :type timeout: int
        :return: Received message
        :rtype: binary
        """
        self.uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        self.uart.reset_input_buffer()
        _cmd = cmd

        for c in _cmd:
            _c = c.encode()
            self.uart.write(_c)
            time.sleep(0.002)
        self.uart.write(b'\r\n')

        # wait for reply
        t0 = time.time()
        while self.uart.in_waiting == 0:
            if (time.time() - t0) > timeout:
                raise ExceptionUART("Timeout! Not received any reply! Perhaps drive is not in BOOT mode. Call with -o")

        _input = b''
        while self.uart.in_waiting:
            _input_bytes = self.uart.in_waiting
            _input += self.uart.read(_input_bytes)
            time.sleep(0.05)
        self.uart.reset_input_buffer()
        self.uart.close()
        return _input

    def __write_file(self, cmd, file_path):
        """
        Sends a file to bootloader.
        :param cmd: Command for bootloader. Either "flash" (app) or "write" (all other files).
        :type cmd: str
        :param file_path: Path to file
        :type file_path: str
        :return: Received message
        :rtype: binary
        """
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
        logger.info("")

        self.uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        self.modem.send_file(file_path)
        time.sleep(0.01)

        res = self.uart.read(self.uart.in_waiting)
        self.uart.close()
        return res

    def __read_file(self, cmd, file_name):
        """
        Read file from flash storage.
        :param cmd: Command for reading (read)
        :type cmd: str
        :param file_name: File which is to be read.
        :type file_name: str
        """

        # Get file size and also check if file is existing on node
        file_size = self.read_file_size(file_name)
        if not file_size:
            logger.error('File not in file system')
            return

        # Calculate timeout. 8000 bytes per second is roughly the speed.
        timeout = (file_size / 8000) + 1
        if timeout < 5:
            timeout = 5

        self._send_cmd('\n')
        cmd += ' ' + file_name
        res = self._send_cmd(cmd)
        self._print(res)

        print()
        self.uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)

        self.modem.recv_file(".")
        time.sleep(0.01)

        if self.uart.in_waiting > 0:
            res = self.uart.read(self.uart.in_waiting)
        self.uart.close()

        return res

    def read_file_size(self, _file):
        """
        Get file size. Call getlist and parse the content.
        :param _file: file name
        :type _file: str
        :return: file size in byte
        :rtype: int
        """
        retry = 5
        while True:
            res = self.send_cmd('getlist')
            res = res.decode(errors='backslashreplace')
            re_res = re.search(rf'{_file}, size: (\d+)', res)
            if re_res:
                return int(re_res.group(1))

            if retry == 0:
                return
            retry -= 1

    def send_cmd(self, cmd):
        """
        Send command to bootloader. Retry on received "Unknown command"
        :param cmd: bootloader command
        :type cmd: str
        :return: Received message
        :rtype: binary
        """
        retry = 5
        while True:
            res = self._send_cmd(cmd)
            if b'Unknown command' not in res or retry == 0:
                break
            retry -= 1
        return res

    def boot(self):
        return self._send_cmd('boot')

    def remove(self, file_name):
        for f in file_name:
            if not self.send_cmd(f'remove {f}'):
                raise ExceptionUART(f'Could not delete file {f}')

    def write_file(self, file_names):
        for f in file_names:
            if not self.__write_file('write', f):
                raise ExceptionUART(f'Could not write file {f}')

    def read_file(self, file_names):
        for f in file_names:
            if not self.__read_file('read', f):
                raise ExceptionUART(f'Could not read file {f}')

    def get_list(self):
        _list = self.send_cmd("getlist")
        file_list = re.findall(r'(.+), size: (\d+)', _list.decode())

        res = list()
        for name, size in file_list:
            res.append({"name": name, "size": int(size)})

        return res

    def flash_fw(self, binary_path=None):
        """
        Flash firmware.
        :param binary_path: Path to firmware
        :type binary_path: str
        :return: Received message
        :rtype: binary
        """
        if not binary_path:
            binary_path = self.__binary_path

        file_name = os.path.basename(binary_path)
        if re.match(r"^package.+\.zip$", file_name, re.M):
            # Unzip package to a temporary directory.
            dtemp = tempfile.mkdtemp(None, 'fw_updater_uart-')
            with zipfile.ZipFile(binary_path) as zf:
                zf.extractall(dtemp)
            binary_path = glob.glob(os.path.join(dtemp, '*.bin'))[0]

        elif not re.match(r'^app.+\.bin$', file_name, re.M):
            raise ExceptionNoBinary(f'Error! "{file_name}" is not a valid binary name. Needs to be "app_*.bin"')

        return self.__write_file('flash', binary_path)

    def remove_fw(self):
        """
        Remove firmware
        :return: Received message
        :rtype: binary
        """
        # Create pseudo binary, which contains only a string and flash this file.
        bin_empty = 'app_empty.bin'
        if not os.path.isfile(bin_empty):
            with open(bin_empty, 'w') as f:
                f.write("void\n")

        return self.__write_file('flash', bin_empty)


def _check_result(res):
    UARTFWUploader._print(res)
    if not res:
        logger.error("...FAILED!")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-d', '--device', dest='device', help='Serial device', type=str, default='ttl232r-3v3-0')
    parser.add_argument('-o', '--hold', dest='hold', help='Stop booting', action='store_true')
    parser.add_argument('-w', '--write', nargs='+', dest='write', metavar='FILE', help='Write <FILE> to device', type=str)
    parser.add_argument('-r', '--read', nargs='+', dest='read', metavar='FILE', help='Read <FILE> on device', type=str)
    parser.add_argument('-a', '--app', dest='app', metavar='APP', help='Flash firmware <APP> to device. Can also be a SOMANET firmware package.', type=str)
    parser.add_argument('-b', '--boot', dest='boot', help='Boot firmware', action='store_true')
    parser.add_argument('-l', '--list', dest='getlist', help='Get file list', action='store_true')
    parser.add_argument('-i', '--info', dest='info', help='Get flash storage info', action='store_true')
    parser.add_argument('-c', '--check', dest='check', help='Check the flash storage', action='store_true')
    parser.add_argument('-v', '--version', dest='version', help='Get bootloader version', action='store_true')
    parser.add_argument('-bh', '--blhelp', dest='help', help='Show bootloader help', action='store_true')
    parser.add_argument('-rm', '--remove', nargs='+', dest='remove', metavar='FILE', help='Remove <FILE> from device', type=str)
    parser.add_argument('-rmb', '--removebinary', dest='remove_bin', help='Remove firmware from device', action='store_true')

    args = parser.parse_args()
    dev = args.device
    uart_fw = UARTFWUploader(dev)

    # Just always send hold
    uart_fw.send_cmd("hold")

    for arg, value in vars(args).items():
        if value is None or not value or arg == "device":
            continue

        if arg == "app":
            logger.info('Flash FW...')
            res = uart_fw.flash_fw(args.app)
            _check_result(res)
        elif arg == "write":
            logger.info(f'Write file {args.write} ...')
            uart_fw.write_file(args.write)
            logger.info(f'Done')
        elif arg == "read":
            logger.info(f'Read file {args.read} ...')
            uart_fw.read_file(args.read)
            logger.info(f'Done')
        elif arg == "boot":
            logger.info('Boot device...')
            res = uart_fw.boot()
            _check_result(res)
        elif arg in ("hold", "check", "info", "version", "help"):
            logger.info(f"{arg}...")
            res = uart_fw.send_cmd(arg)
            _check_result(res)
        elif arg == "getlist":
            logger.info(f"Get file list ...")
            print(uart_fw.get_list())
        elif arg == "remove":
            logger.info(f'Remove "{args.remove}" from device...')
            uart_fw.remove(args.remove)
        elif arg == "remove_bin":
            logger.info("Remove app from device...")
            uart_fw.remove_fw()
        else:
            parser.print_help()
