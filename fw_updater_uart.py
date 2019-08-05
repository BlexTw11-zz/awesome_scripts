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


def printStdErr(*objs):
#    print("", *objs, file=stderr)
    print("")

def asbyte(v):
    return chr(v & 0xFF)



class LightYModem:
    """
    Receive_Packet
    - first byte SOH/STX (for 128/1024 byte size packets)
    - EOT (end)
    - CA CA abort
    - ABORT1 or ABORT2 is abort

    Then 2 bytes for seq-no (although the sequence number isn't checked)

    Then the packet data

    Then CRC16?

    First packet sent is a filename packet:
    - zero-terminated filename
    - file size (ascii) followed by space?
    """

    soh = 1     # 128 byte blocks
    stx = 2     # 1K blocks
    eot = 4
    ack = 6
    nak = 0x15
    ca =  0x18          # 24
    crc16 = 0x43        # 67
    abort1 = 0x41       # 65
    abort2 = 0x61       # 97

    packet_len = 1024
    expected_packet_len = packet_len+5
    packet_mark = stx

    def __init__(self):
        self.seq = None
        self.ymodem = None

    def flush(self):
        pass
        #self.ymodem.flush()

    def blocking_read(self):
        ch = ''
        while not ch:
            ch = self.ymodem.read(1)
        printStdErr("read %d " % ord(ch))
        return ch

    def _read_response(self):
        ch1 = self.blocking_read()
        ch1 = ord(ch1)
        printStdErr("response %d" % (ch1))

        if ch1==LightYModem.ack and self.seq==0:    # may send also a crc16
            ch2 = self.blocking_read()
        elif ch1==LightYModem.ca:                   # cancel, always sent in pairs
            ch2 = self.blocking_read()
        return ch1

    def write(self, packet):
        for x in range(len(packet)):
            self.ymodem.write(packet[x])

        return len(packet);

    def _send_ymodem_packet(self, data):
        # pad string to 1024 chars
        data = data.ljust(LightYModem.packet_len)
        print(len(data))
        seqchr = asbyte(self.seq & 0xFF)
        seqchr_neg = asbyte((-self.seq-1) & 0xFF)
        crc16 = '\x00\x00'
        print("data", type(data))
        packet = asbyte(LightYModem.packet_mark) + seqchr + seqchr_neg + data + crc16

        if len(packet)!=LightYModem.expected_packet_len:
            raise Exception("packet length is wrong! %d" % len(packet))

        written = self.write(packet)
        printStdErr("sent packet data, flush..."+str(written))
        self.flush()
        printStdErr("wait response..")
        response = self._read_response()
        if response==LightYModem.ack:
            ("sent packet nr %d " % (self.seq))
            self.seq += 1
        return response

    def _send_close(self):
        self.ymodem.write(asbyte(LightYModem.eot))
        self.flush()
        response = self._read_response()
        if response == LightYModem.ack:
            self.send_filename_header("", 0)
            self.ymodem.close()

    def send_packet(self, file, output):
        response = LightYModem.eot
        data = file.read(LightYModem.packet_len)
        if len(data):
            response = self._send_ymodem_packet(data)
        return response

    def send_filename_header(self, name, size):
        self.seq = 0
        packet = name + asbyte(0) + str(size) + ' '
        return self._send_ymodem_packet(packet)

    def transfer(self, file, ymodem, output):
        self.ymodem = ymodem
        """
        file: the file to transfer via ymodem
        ymodem: the ymodem endpoint (a file-like object supporting write)
        output: a stream for output messages
        """

        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(0, os.SEEK_SET)
        response = self.send_filename_header("binary", size)
        while response==LightYModem.ack:
            response = self.send_packet(file, output)

        file.close()
        if response==LightYModem.eot:
            self._send_close()

        return response

def ymodem(serial, filename):
    file = open(filename, 'rb')
    result = LightYModem().transfer(file, serial, sys.stderr)
    file.close()
    print("result: " + str(result))

    try:
        while (True):
            print(ser.read())
    except:
        pass
    print("Done")




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

    def forward_to_cmd(self, ser, proc):
        while True:
            try:
                proc.stdin.write(ser.read())
                proc.stdin.flush()
            except IOError as e:
                if e.errno == errno.EPIPE:
                    break

    def _call(self, args, uart, timeout=None):
        if not timeout:
            timeout = self.__timeout
        #return sp.check_output(args, shell=True, universal_newlines=True, timeout=timeout)
        proc = sp.Popen(args, stdin=sp.PIPE, stdout=sp.PIPE)

        fwc = threading.Thread(target=self.forward_to_cmd, args=(uart,proc,))
        fwc.start()

        self.forward_to_serial(uart, proc)
        fwc.join()
        

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
        #input('wait')
        #self._call('stty -F %s %d' % (self.__port, self.__baudrate))
        #self._call('%s %s -k  > %s < %s' % (self.__modem, file_path, self.__port, self.__port))
        self._call([self.__modem, file_path], uart)
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
            raise ExceptionNoBinary('Error! "%s" is not a valid binary name. Needs to be "app_*.bin"' % binary_path)
        return self.__write_file('flash', binary_path) != ''

    def write_file(self, file_path):
        
        if re.match(r'^app.+\.bin$', file_path, re.M):
            raise ExceptionNoBinary('Error! "%s" is a binary name. To flash binary use "-f"' % file_path)
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


