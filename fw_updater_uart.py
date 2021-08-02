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

# logging.basicConfig(stream=sys.stderr, level=logging.INFO, format='[%(levelname)s]: %(message)s')
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


class ExceptionUART(Exception):
    pass


class ExceptionNoBinary(ExceptionUART):
    pass


class ExceptionLRZSZMissing(ExceptionUART):
    pass


class UARTFWUploader(object):

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
            self.__binary_path = self._test_test_path(binary_path)
       
        self.__port = '' 
        if '/dev/' not in serial:
            self.__port = '/dev/'
        self.__port += serial
        if not os.path.exists(self.__port):
            raise ExceptionUART(f"Device \"{self.__port}\" does not exists")
        self.__modem_write = 'sb'
        self.__modem_read = 'rb'
        self.__baudrate = baudrate

        self._test_lrzsz_installation()

    @staticmethod
    def _test_test_path(path):
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

    def _test_lrzsz_installation(self):
        """
        Check, if lrzsz (YMODEM) is installed.
        If not, ExceptionLRZSZMissing is raised.
        """
        if sp.call('command -v %s' % self.__modem_write, shell=True, stdout=sp.DEVNULL) != 0:
            raise ExceptionLRZSZMissing("lrzsz not installed! Call \"apt install lrzsz\"")

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
                    logger.info('>>> ' + l)
            else:
                logger.info('-')
        except UnicodeDecodeError:
            logger.error(f'Error: {res}')

    def forward_to_serial(self, ser, proc):
        """
        Reads YMODEM command from stdout and sends it to serial device.
        Code found in internet!
        :param ser: serial device
        :type ser: serial.Serial()
        :param proc: subprocess, which is running YMODEM (sb, rb)
        :type proc: subprocess.Popen
        """
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
        """
        Reading messages from serial device and sends it through stdin to YMODEM.
        Code found in internet!
        :param ser: serial device
        :type ser: serial.Serial()
        :param proc: subprocess, which is running YMODEM (sb, rb)
        :type proc: subprocess.Popen
        """
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
        """
        Starts YMODEM in process and forward_to_app() in a thread.
        Runs forward_to_serial() itself.
        Code found in internet!
        :param args: YMODEM Arguments
        :type args: list
        :param ser: serial device
        :type ser: serial.Serial()
        """
        proc = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE)

        fwc = threading.Thread(target=self.forward_to_app, args=(uart,proc,))
        fwc.start()

        self.forward_to_serial(uart, proc)

        fwc.join()

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
                raise ExceptionUART("Timeout! Not received any reply!")

        _input = b''
        while uart.in_waiting:
            _input_bytes = uart.in_waiting
            _input += uart.read(_input_bytes)
            time.sleep(0.05)
        uart.reset_input_buffer()
        uart.close()
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

        uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        self._call([self.__modem_write, file_path], uart)
        time.sleep(0.01)

        res = uart.read(uart.in_waiting)
        uart.close()
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
        cmd += ' '+file_name
        res = self._send_cmd(cmd)
        self._print(res)

        print()
        uart = serial.Serial(self.__port, self.__baudrate, timeout=timeout)
        modem = [self.__modem_read, '-E', '-t', str(int(timeout*10))]

        self._call(modem, uart)
        time.sleep(0.01)

        if uart.in_waiting > 0:
            res = uart.read(uart.in_waiting)
        uart.close()

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
            re_res = re.search(r'%s, size: (\d+)' % _file, res)
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

    def get_list(self):
        return self.send_cmd('getlist')

    def get_info(self):
        return self.send_cmd('info')

    def check(self):
        return self.send_cmd('check')

    def boot(self):
        return self._send_cmd('boot')

    def remove(self, file_name):
        for f in file_name:
            if not self.send_cmd(f'remove {f}'):
                raise ExceptionUART(f'Could not delete {f}')

    def write_file(self, file_names):
        for f in file_names:
            if not self.__write_file('write', f):
                raise ExceptionUART(f'Could not write file {f}')

    def read_file(self, file_names):
        for f in file_names:
            if not self.__read_file('read', f):
                raise ExceptionUART(f'Could not read file {f}')

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

        if re.match(r"^package.+\.zip$", binary_path, re.M):
            # Unzip package to a temporary directory.
            dtemp = tempfile.mkdtemp(None, 'fw_updater_uart-')
            with zipfile.ZipFile(binary_path) as zf:
                zf.extractall(dtemp)
            binary_path = glob.glob(dtemp + '/*.bin')[0]    


        elif not re.match(r'^app.+\.bin$', binary_path, re.M):
            raise ExceptionNoBinary('Error! "%s" is not a valid binary name. Needs to be "app_*.bin"')

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
    parser.add_argument('-a', dest='app', metavar='FILE', help='flash "FILE" to device', type=str)
    parser.add_argument('-w', nargs='+', dest='write', metavar='FILE', help='write "FILE" to device', type=str)
    parser.add_argument('-r', nargs='+', dest='read', metavar='FILE', help='read "FILE" on device', type=str)
    parser.add_argument('-d', dest='device', help='serial device', type=str, default='ttl232r-3v3-0')
    parser.add_argument('-b', dest='boot', help='boot device', action='store_true')
    parser.add_argument('-l', dest='getlist', help='get file list', action='store_true')
    parser.add_argument('-i', dest='info', help='get flash storage info', action='store_true')
    parser.add_argument('-c', dest='check', help='Check the flash storage', action='store_true')
    parser.add_argument('-rm', nargs='+', dest='remove', metavar='FILE', help='remove "FILE" from device', type=str)
    parser.add_argument('-rmb', dest='remove_bin', help='remove app from device', action='store_true')

    args = parser.parse_args()
    dev = args.device
    uart_fw = UARTFWUploader(dev)
    if args.app:
        logger.info('Flash FW...')
        res = uart_fw.flash_fw(args.app)
        _check_result(res)
    elif args.write:
        logger.info('Write file...')
        uart_fw.write_file(args.write)
    elif args.read:
        logger.info('read file...')
        uart_fw.read_file(args.read)
    elif args.boot:
        logger.info('Boot device...')
        res = uart_fw.boot()
        _check_result(res)
    elif args.getlist:
        logger.info('Get List...')
        res = uart_fw.get_list()
        _check_result(res)
    elif args.check:
        logger.info('Check flash storage...')
        uart_fw.check()
    elif args.info:
        logger.info('Get info...')
        res = uart_fw.get_info()
        _check_result(res)
    elif args.remove:
        logger.info('Remove "%s" from device...' % args.remove)
        uart_fw.remove(args.remove)
    elif args.remove_bin:
        logger.info("Remove app from device...")
        uart_fw.remove_fw()
    else:
        parser.print_help()


