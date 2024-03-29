# Look through a dictionary, and get elevations for all MGRS coordinates, add them to file.


'''
Some example Strings

    ["DictKey_1013"] = "Chalice 3 (AWACS): Boar flight, Chalice 3, new tasking. U.S. ground forces are moving to interdict an enemy camp in a mountain village, grid: \
\
37T FJ 567 286.\
N43 35.715' E040 56.413'\
\
Your task is to eliminate hostile air defenses and high value assets in contact with friendly troops. Check-in with Anvil 4 on frequency 032 FM and execute his requests. Expect Type II engagements danger close to friendly positions. Anvil 4 is reporting moderate air defenses on target. Chalice 3, out. ",
    ["DictKey_637"] = "",
    ["DictKey_1510"] = "38T LN 731 166",

'''
import argparse
import mgrs
import requests
import dbm
import re
import time
import logging

from mizlib import Mizlib

class MGRSElev():

    def __init__(self,mizfile,logger,cachedb=None):
        self.mizfile = mizfile
        self.mgrs = mgrs.MGRS()
        self.ml = Mizlib(mizfile,'',logger)
        self.logger = self.ml.logger
        if cachedb:
            self.dbm_filename = cachedb
        else:
            self.dbm_filename = 'mgrs_cache.db'
        self.db_handle = dbm.open(self.dbm_filename, 'c')

    def dbm_flush(self):
        self.db_handle.close()
        self.db_handle = dbm.open('mgrs_cache.db', 'c')

    def doit(self):
        mgrs_pattern = re.compile(r'(.*)(\d{2}[A-Z]\s[A-Z]{2}\s\d+\s\d+)(.*)')
        logger.debug("in doit")
        # Pull out the 'dictionary' from the mizfile
        my_dict = self.ml.extract_filedict_from_miz('l10n/DEFAULT/dictionary')
        # Parse the dictionary for MGRS coordinates - ones that arent already with elevations
        # Get the elevation for each MGRS coordinate, checking cache
        for key in my_dict:
            if '37T' in my_dict[key] or '38T' in my_dict[key]:
            #if True:
                print(key,my_dict[key])
                
                if mgrs_pattern.match(my_dict[key]):
                    print("Matched")
                    mgrs_coords = mgrs_pattern.findall(my_dict[key])
                    print(mgrs_coords)
                    for coord in mgrs_coords:
                        print(coord)
                        coord_key = coord[1].replace(' ','')
                        lat,lon = self.mgrs.toLatLon(coord_key)
                        print(lat,lon)
                        if self.get_key(coord_key) != None:
                            print("Already have elevation")
                            continue
                        else:
                            elev = self.get_elev_lat_lon(lat,lon)
                            print(elev)
                            self.set_key(coord_key,elev)
                        print(self.get_key(coord_key))
                # break
        self.dbm_flush()
        print(my_dict.keys())
        print(len(self.db_handle.keys()))
        print(self.db_handle.keys())

        # Now go key-by-key, match for key but not elevation string. replace value.
        for key in my_dict:
            mgrs_coords = mgrs_pattern.findall(my_dict[key])
            for coord in mgrs_coords:
                coord = coord[1]
                print(coord)
                coord_key = coord.replace(' ','')
                # if the string is there but '- \dft' is not, add it
                if not re.search(r'{coord} - \d+ft',my_dict[key]):
                    print(f"Adding elevation to {coord}")
                    my_dict[key] = my_dict[key].replace(coord, f"{coord} - {self.get_key(coord_key)}ft")

                    print(my_dict[key])

        # Write the dictionary back to the miz file
        self.ml.inject_filedict_into_miz(self.ml.miz_file,'l10n/DEFAULT/dictionary', my_dict)

 
    def get_elev_lat_lon(self,lat,lon):
        # Use an API to get the elevation of a lat/lon
        url = f'https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}'
        r = requests.get(url)
        elevation = r.json()['results'][0]['elevation']
        # convert from meters to feet
        elevation = elevation * 3.28084
        # round elevation to nearest foot
        elevation = round(elevation)
        # Be kind to the API endpoint
        time.sleep(1)
        return elevation


    def get_key(self,key):
        try:
            return self.db_handle[key].decode("utf-8")
        except KeyError:
            return None
        

    def set_key(self,key,value):
        print(f"Setting {key} to {value}")
        self.db_handle[key] = str(value)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if args.debug:
        logger.setLevel(logging.DEBUG)

    mg = MGRSElev(args.filename, logger)

    mg.doit()
