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
        terrain = Nevada()
        mp = mapping.Point(0,0,terrain)
        ll = mapping.LatLng(36,-115)
        mp = mp.from_latlng(ll,terrain)
        #terrain._ll_to_point_transformer(-360507.203125, -75590.070313)

        #lat_lon_to_x_z = Transformer.from_crs(wgs84, crs)
        #tra = Transformer.from_crs(
        #    CRS("WGS84"), terrain.projection_parameters.to_crs()
        #)

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
        #my_dict = self.ml.extract_filedict_from_miz('mission')
        self.logger.debug("in hide")
        self.logger.debug(self.config)
        # DEBUG:
        my_polygon = None
        spawnrange_name = None
        for range, v in self.config['ranges'].items():
            self.logger.debug(range)
            my_polygon = self.get_polygon(v['prefix'],v['polygon'])
            spawnrange_name = f"!*{range}*!"
            self.logger.debug(my_polygon)

        
        my_dict = self.ml.extract_filedict_from_miz('mission')
        # Iterate over groups.. Conditions for hiding are:
        # 1. Group is a ground unit
        # 2. Group is not late_activation
        # 3. Group is within polygon
        self.logger.debug(my_dict.keys())
        self.logger.debug(my_dict['coalition']['red']['country'][1]['vehicle']['group'][1].keys())
        with open('miz_dump.json','w') as f:
            #f.write(json.dumps(my_dict,indent=2))
            f.write(json.dumps(my_dict['coalition']['red']['country'][1]['vehicle']['group'][1],indent=2))

        # How to get coordinate system??

        '''
        stuff we care about
            "y": -86291.714285714,
            "x": -348996.85714286,
            "name": "65-01",
            "visible": false,
            "hidden": true,
            ["lateActivation"] = true, NOTE this key is not present unless explicitly set to true
        '''
        
        for country_id, country in my_dict['coalition']['red']['country'].items():
            if not 'vehicle' in country:
                continue
            for group_id, group in country['vehicle']['group'].items():
                #self.logger.debug(group.keys())
                if 'y' in group:
                    point = Point(group['x'],group['y'])
                    if my_polygon.contains(point):
                        self.logger.debug(f"In Poly {group['name']}")
                        #group['hidden'] = True
                        #group['visible'] = False
                        group['lateActivation'] = True
                        group['name'] = spawnrange_name+group['name']
                        #self.logger.debug(group)
                        self.logger.debug(json.dumps(group,indent=2))
                    else:
                        #self.logger.debug(f"Not in Poly {group['name']}")
                        pass
        #json.dumps(my_dict)
        #self.logger.debug(json.dumps(my_dict['coalition']['red']['country'].keys(), indent=2)) #['Russia']['category']['Ground Units']['group'])

        # Check if my changes made it in the mission object.
        with open('miz_dump.json','w') as f:
            #f.write(json.dumps(my_dict,indent=2))
            f.write(json.dumps(my_dict,indent=2))
            #print(polygon.contains(point))
            #self.logger.debug(self.config['ranges'][key])

                #self.logger.debug(self.get_elev_lat_lon(lat,lon))
                #self.set_key(coord,0)
        #lat,lon = self.mgrs.toLatLon(coord_key)
        # read a config file
        #pass
            
        #self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def unhide(self):
        # read config, find all 'keys' find any ground unit with name of key,
        # remove the key from the name, and set the unit to not be late activated.
        pass



if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument('action',choices=['hide','unhide'],help='Action to perform')
    parser.add_argument('conffile',help='Configuration file')
    parser.add_argument('filename')
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
    else:
        print("Unknown action")
        exit(1)


