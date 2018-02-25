import gspread
from oauth2client.service_account import ServiceAccountCredentials
 

class Goller(object):

    def __init__(self):
        self.__sheet_name = 'goller_test'
        self.__keyfile = 'gollertest-c6e33b844feb.json'
        self.__order_list = self.get_google_list()

    def get_google_list(self):
        # use creds to create a client to interact with the Google Drive API
        scope = ['https://spreadsheets.google.com/feeds']
        creds = ServiceAccountCredentials.from_json_keyfile_name(self.__keyfile, scope)
        client = gspread.authorize(creds)
         
        # Find a workbook by name and open the first sheet
        # Make sure you use the right name here.
        sheet = client.open(self.__sheet_name).sheet1
         
        # Extract and print all of the values
        list_of_hashes = sheet.get_all_values()
        return list_of_hashes

    def reformate_list(self):
        new_list = []
        state = 0
        dict_day = {}
        for i, l in enumerate(self.__order_list):
            if state == 0:
                if l[0] == 'week':
                    dict_day = {'date': [], 'menu1': [], 'menu2': [], 'menu3': [], 'menu4': [], 'menu5': []}
                    state = 1
            elif state == 1:
                empty_line = True
                for f in l:
                    if f != '':
                        empty_line = False

                if not empty_line:
                    def filter_entry(entry, val):
                        if val != '':    
                            dict_day[entry].append(val)

                    filter_entry('date', l[0])
                    filter_entry('menu1',l[1])
                    filter_entry('menu2',l[2])
                    filter_entry('menu3',l[3])
                    filter_entry('menu4',l[4])
                    filter_entry('menu5',l[5])
                    state = 1

                if i == len(self.__order_list)-1 or empty_line:
                    new_list.append(dict_day)
                    state = 0
        return new_list

    def print_list(self):
        for l in self.__order_list:
            print(l)


if __name__ == '__main__':
    goller = Goller()
    l = goller.reformate_list()
    for e in l:
        for key, val in e.items():
            print(key, val)
        print()