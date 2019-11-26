#!/usr/bin/python3
from pyworktimer_modules.google_drive import GoogleCalc
import datetime
import argparse
import os 
dir_path = os.path.dirname(os.path.realpath(__file__))

FILE_ID = '1eA_842Yg7dVu1-KEg3eQ_z62UUUCP834cfz17NncuBE'
AUTH_FILE = dir_path + '/pyworktimer_modules/' + 'pyworktimer-9abd2337e580.json'
APP_VERSION = 0.1

class PyWorkTimer():

    START_TIME = 2
    END_TIME = 3

    def __init__(self):

        self.now = datetime.datetime.now().strftime('%H:%M')
        self.today = datetime.datetime.now().strftime('%d.%m.%Y')
        self.year = datetime.datetime.now().strftime('%Y')
        self.gcalc = GoogleCalc(AUTH_FILE, FILE_ID)
        self.gcalc.open_file()

        sheets = self.gcalc._get_worksheet_names()
        for sh in sheets:
            if self.year in sh:
                self.gcalc.open_sheet(sh)
                break

    def _set_time(self, start_end, no_update=True):
        cell = self.gcalc.find(self.today)

        row = self.gcalc.get_row_values(cell.row)

        if row[start_end] != '' and no_update:
            print("Already written")
            return 

        self.gcalc.write(cell.row, start_end+1, self.now)
        print("Done")

    def set_start_time(self):
        self._set_time(self.START_TIME)

    def set_end_time(self):
        self._set_time(self.END_TIME)

    def update_start_time(self):
        self._set_time(self.START_TIME, False)

    def update_end_time(self):
        self._set_time(self.END_TIME, False)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='PyWorkTimer.\nv%d' % APP_VERSION)
    parser.add_argument('--start', '-s',
                        action='store_true',
                        help='Write start time')

    parser.add_argument('--end', '-e',
                        action='store_true',
                        help='Write end time')

    parser.add_argument('--update_start', '-u',
                        action='store_true',
                        help='Update start time')

    parser.add_argument('--update_end', '-d',
                        action='store_true',
                        help='Update end time')

    args = parser.parse_args()
    pytimer = PyWorkTimer()

    if args.start:
        pytimer.set_start_time()
    elif args.end:
        pytimer.set_end_time()
    elif args.update_start:
        pytimer.update_start_time()
    elif args.update_end:
        pytimer.update_end_time()


