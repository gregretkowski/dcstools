'''
This is a script which can take from a bounded-box of coordinates, a set of ranges,
and make the units late activation and set their name as appropriate for a 
spawnrange script to spawn despawn them..

https://github.com/Markoudstaal/DCS-Simple-Spawn-Menu#how-it-works

'''


import argparse
import mgrs
#import requests
#import dbm
import re
#import time
import logging
import yaml
import json

from shapely.geometry import Point
from shapely.geometry.polygon import Polygon

from dcs.terrain import Terrain
from dcs.terrain.nevada import Nevada
import dcs.mapping as mapping
from pyproj import CRS, Transformer

from mizlib import Mizlib

class HideRange():

    def __init__(self,conffile, mizfile,logger):
        with open(conffile) as f:
            self.config = yaml.safe_load(f)

        self.mizfile = mizfile
        self.mgrs = mgrs.MGRS()
        self.ml = Mizlib(mizfile,'',logger)
        self.logger = self.ml.logger


    def get_polygon(self,mgrs_prefix,mgrs_list):

        #terrain = Terrain(self.config['terrain'])
        # FIXME -- this is hardcoded for Nevada
        if self.config['terrain'] == 'NTTR':
            terrain = Nevada()
        else:
            raise Exception("Unsupported terrain.. you need to add it")
        mp = mapping.Point(0,0,terrain)
        ll = mapping.LatLng(36,-115)
        mp = mp.from_latlng(ll,terrain)

        self.logger.debug(mp.latlng())
        #raise SystemExit
        coord_list = []
        for coord in mgrs_list:
            self.logger.debug(mgrs_prefix+coord)
            lat,lon = self.mgrs.toLatLon(mgrs_prefix+coord)
            self.logger.debug(lat)
            self.logger.debug(lon)
            # Convert lat/lon to x/y

            mp = mapping.Point(0,0,terrain)
            ll = mapping.LatLng(lat,lon)
            mp = mp.from_latlng(ll,terrain)
                
            coord_list.append((mp.x,mp.y))
        return Polygon(coord_list)


    def hide(self):

        self.logger.debug("in hide")
        self.logger.debug(self.config)

        ranges = {}
        for range, v in self.config['ranges'].items():
            self.logger.debug(range)
            my_polygon = self.get_polygon(self.config['prefix'],v['polygon'])
            spawnrange_name = f"!*{range}*! "
            # Nested ranges arent working.
            #spawnrange_name = f"!?GroundRanges?*{range}*! "
            self.logger.debug(my_polygon)
            ranges[spawnrange_name] = my_polygon

        # Create a set of polygons to modify stuff.. range_name, polygon.
        
        # Load mission and iterate over groups.        
        my_dict = self.ml.extract_filedict_from_miz('mission')

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                if not 'vehicle' in country:
                    continue
                for group_id, group in country['vehicle']['group'].items():
                    #self.logger.debug(group.keys())
                    if 'y' in group:
                        point = Point(group['x'],group['y'])
                        
                        # 1. Group is a ground unit
                        # 2. Group is not late_activation
                        # 3. Group is within polygon
                        for spawnrange_name, my_polygon in ranges.items():
                            #if my_polygon.contains(point) and not 'lateActivation' in group and not spawnrange_name in group['name']:
                            # Some stuff was late activation anyway. I dont know why, but I am gonna include them anyway
                            if my_polygon.contains(point) and not spawnrange_name in group['name']:
                                #ranges[spawnrange_name] = my_polygon

                                self.logger.debug(f"Applying to {group['name']}")
                                #group['hidden'] = True
                                #group['visible'] = False
                                group['lateActivation'] = True
                                group['name'] = spawnrange_name+group['name']
                                logging.info(f"added {group['name']}")
                                #self.logger.debug(group)
                                self.logger.debug(json.dumps(group,indent=2))
                            else:
                                #self.logger.debug(f"Not in Poly {group['name']}")
                                pass
            
        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def unhide(self):
        # read config, find all 'keys' find any ground unit with name of key,
        # remove the key from the name, and set the unit to not be late activated.
        ranges = {}
        for range, v in self.config['ranges'].items():
            spawnrange_name = f"!*{range}*!"
            ranges[spawnrange_name] = ""

        my_dict = self.ml.extract_filedict_from_miz('mission')

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                if not 'vehicle' in country:
                    continue
                for group_id, group in country['vehicle']['group'].items():
                    if not 'y' in group:
                        continue
                    for spawnrange_name, my_polygon in ranges.items():
                        if spawnrange_name in group['name']:
                            group['name'] = group['name'].replace(spawnrange_name,'')
                            del group['lateActivation']
                            logging.info(f"removed {spawnrange_name} from {group['name']}")

        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def deact(self):

        # Remove 'ACTIVE_' from the name of the group, and remove lateActivation.. deals
        # with the script that auto activates these groups and is no longer needed.
        my_dict = self.ml.extract_filedict_from_miz('mission')

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                if not 'vehicle' in country:
                    continue
                for group_id, group in country['vehicle']['group'].items():
                    if not 'y' in group:
                        continue

                    if 'ACTIVE_' in group['name']:
                        group['name'] = group['name'].replace('ACTIVE_','')
                        del group['lateActivation']
                        logging.info(f"removed 'ACTIVE_' from {group['name']}")

        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['hide','unhide','deact'],help='Action to perform')
    parser.add_argument('conffile',help='Configuration file')
    parser.add_argument('filename')
    parser.add_argument('--include-la', '-a', action='store_true', help='Include already late activated units in the hide action.')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    hr = HideRange(args.conffile, args.filename, logger)
    if args.action == 'hide':
        hr.hide()
    elif args.action == 'unhide':
        hr.unhide()
    elif args.action == 'deact':
        hr.deact()
    else:
        print("Unknown action")
        exit(1)


