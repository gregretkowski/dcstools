DESCRIPTION='''
This script will export all 'client' radio configs from a mission, or
will import. It handles multiple airframes.

'''

# python .\radiomgr.py export radios.yml ..\OA-Syria_Training_Map\Syria_Training.miz --debug
# python .\radiomgr.py import radios.yml '..\Saved Games\DCS.openbeta\Missions\OA-Caucusus-Bactria.miz' --debug

import argparse
#import mgrs
#import requests
#import dbm
import re
#import time
import logging
import yaml
import json

#from shapely.geometry import Point
#from shapely.geometry.polygon import Polygon

#from dcs.terrain import Terrain
#from dcs.terrain.nevada import Nevada
#import dcs.mapping as mapping
#from pyproj import CRS, Transformer

from mizlib import Mizlib

class RadioMgr():

    def __init__(self,conffile, mizfile,logger):
        self.conffile = conffile
        '''
        with open(conffile) as f:
            self.config = yaml.safe_load(f)
        '''
        self.mizfile = mizfile
        #self.mgrs = mgrs.MGRS()
        self.ml = Mizlib(mizfile,'',logger)
        self.logger = self.ml.logger


    def export_radios(self,filter=None):

        self.logger.debug("in export")
        #self.logger.debug(self.config)

        airframes = {}

        # Load mission and iterate over groups.        
        my_dict = self.ml.extract_filedict_from_miz('mission')

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                #self.logger.debug(json.dumps(country,indent=2))
                if not 'plane' in country:
                    continue
                for group_id, group in country['plane']['group'].items():
                    if not 'Radio' in group['units'][1]:
                        continue
                    if filter and not re.match(re.compile(filter), group['name']):
                        continue
                    dump_this = [
                        group['units'][1]['skill'], group['units'][1]['type']
                    ]
                    self.logger.debug(json.dumps(dump_this,indent=2))
                    #self.logger.debug(json.dumps(group,indent=2))
                    if group['units'][1]['skill'] == 'Client':
                        #self.logger.debug(json.dumps(group['units'][1], indent=2))
                        self.logger.debug(json.dumps(group['units'][1]["Radio"], indent=2))
                        airframes[ group['units'][1]['type'] ] = group['units'][1]["Radio"]
                        #raise Exception

        self.logger.debug(json.dumps(airframes, indent=2))
        self.logger.info(f"Writing {len(airframes)} airframes to {self.conffile}")
        yaml.dump(airframes, open(self.conffile,'w'), default_flow_style=False)
                    

        # self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def import_radios(self,filter=None):
        self.logger.debug("in export")
        #self.logger.debug(self.config)

        airframes = {}

        self.logger.info(self.conffile)
        with open(self.conffile) as f:
            file_text = f.read()
            try:
                self.config = yaml.safe_load(file_text)
            except yaml.scanner.ScannerError as e:
                json_confg = json.loads(file_text)
                # convert format
                self.config = {}
                for k,v in json_confg.items():
                    radios = [rad['channels'] for rad in v['radios']]
                    self.config[v]['type'] = radios
                raise Exception('I give up implementing json format')
            


        # Load mission and iterate over groups.        
        my_dict = self.ml.extract_filedict_from_miz('mission')

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                #self.logger.debug(json.dumps(country,indent=2))
                if not 'plane' in country:
                    continue
 
                for group_id, group in country['plane']['group'].items():
                    if not 'Radio' in group['units'][1]:
                        continue
                    if filter and not re.match(re.compile(filter), group['name']):
                        continue
                    

                    for unit_id, unit in group['units'].items():
                        if unit['skill'] == 'Client' and unit['type'] in self.config:
                            self.logger.debug(f"Setting {unit['type']} to {self.config[unit['type']]}")
                            unit['Radio'] = self.config[unit['type']]
                            self.logger.info(f"Updated {unit['type']} {unit['name']}")
                

        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('action',choices=['export','import'],help='Action to perform')
    parser.add_argument('conffile',help='Configuration file')
    parser.add_argument('filename')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')
    parser.add_argument('--filter', '-f', metavar='AIRFRAME', default=None, help='Filter for a specific airframe')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    rm = RadioMgr(args.conffile, args.filename, logger)
    if args.action == 'export':
        rm.export_radios(args.filter)
    elif args.action == 'import':
        rm.import_radios(args.filter)
    else:
        print("Unknown action")
        exit(1)


