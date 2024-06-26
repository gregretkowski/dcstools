DESCRIPTION='''
This script will:
* export all 'client' radio configs from a mizfile into a YAML
* import radio configs from a YAML into a mizfile

will import. It handles multiple airframes.

'''

# python .\radiomgr.py export radios.yml ..\OA-Syria_Training_Map\Syria_Training.miz --debug
# python .\radiomgr.py import radios.yml '..\Saved Games\DCS.openbeta\Missions\OA-Caucusus-Bactria.miz' --debug

import argparse
#import mgrs
#import requests
#import dbm
import os
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
        if os.path.exists(self.conffile):
            airframes_orig = yaml.safe_load(open(self.conffile))
        else:
            airframes_orig = {}
        

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

        new_airframe_count = len(airframes)
        airframes = self.ml.deep_merge(airframes_orig, airframes)
        self.logger.debug(json.dumps(airframes, indent=2))
        self.logger.info(f"Writing {new_airframe_count} airframes to {self.conffile}")
        yaml.dump(airframes, open(self.conffile,'w'), default_flow_style=False)
                    

        # self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def filter_jets(self,my_dict, filter=None):

        for coalition_id, coalition in my_dict['coalition'].items():
            for country_id, country in coalition['country'].items():
                #self.logger.debug(json.dumps(country,indent=2))
                if not 'plane' in country:
                    continue
 
                for group_id, group in country['plane']['group'].items():
                    #if not 'Radio' in group['units'][1]:
                    #    continue
                    if filter and not re.match(re.compile(filter), group['name']):
                        continue
                    yield group

    def export_waypoints(self,filter=None):
        self.logger.debug("in export")
        #self.logger.debug(self.config)
        airframes = {}
        if os.path.exists(self.conffile):
            airframes_orig = yaml.safe_load(open(self.conffile))
        else:
            airframes_orig = {}

        my_dict = self.ml.extract_filedict_from_miz('mission')
        
        for group in self.filter_jets(my_dict,filter):
            self.logger.debug(json.dumps(group['route']['points'], indent=2))
            self.logger.debug(json.dumps(group['name'], indent=2))

            airframes[ group['units'][1]['type'] ] = group['route']['points']
        
        new_airframe_count = len(airframes)
        airframes = self.ml.deep_merge(airframes_orig, airframes)
        self.logger.debug(json.dumps(airframes, indent=2))
        self.logger.info(f"Writing {new_airframe_count} airframes to {self.conffile}")
        yaml.dump(airframes, open(self.conffile,'w'), default_flow_style=False)


    def import_waypoints(self,filter=None):

        with open(self.conffile) as f:
            file_text = f.read()
            self.config = yaml.safe_load(file_text)

        my_dict = self.ml.extract_filedict_from_miz('mission')

        for group in self.filter_jets(my_dict,filter):
            self.logger.debug(json.dumps(group['route']['points'], indent=2))
            self.logger.debug(json.dumps(group['name'], indent=2))

        # NOTE - we have to skip the first point, as it is the start point.

        # Load mission and iterate over groups.        
        my_dict = self.ml.extract_filedict_from_miz('mission')

        for group in self.filter_jets(my_dict,filter):
            if not 'Radio' in group['units'][1]:
                continue
            for unit_id, unit in group['units'].items():
                if unit['skill'] == 'Client' and unit['type'] in self.config:
                    #self.logger.debug(json.dumps(group['route']['points'], indent=2))
                    first_waypoint = group['route']['points'][1]
                    group['route']['points'] = self.config[unit['type']]
                    group['route']['points'][1] = first_waypoint
                    self.logger.info(f"Updated {unit['type']} {unit['name']}")

        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)


    def import_radios(self,filter=None):
        self.logger.debug("in import")
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

        for group in self.filter_jets(my_dict,filter):
            if not 'Radio' in group['units'][1]:
                continue
            for unit_id, unit in group['units'].items():
                if unit['skill'] == 'Client' and unit['type'] in self.config:
                    old_radio_1 = unit['Radio'][1]['channels'][1]
                    new_radio_1 = self.config[unit['type']][1]['channels'][1]
                    self.logger.debug(f"Setting {unit['type']} to {self.config[unit['type']]}")
                    unit['Radio'] = self.config[unit['type']]
                    self.logger.info(f"Updated {unit['type']} {unit['name']}")
                    #self.logger.info(f"{old_radio_1} -> {new_radio_1}")
                    if 'frequency' in group.keys() and group['frequency'] != new_radio_1:
                        self.logger.info(f"Updated Group frequency {group['frequency']} -> {new_radio_1}")
                        group['frequency'] = new_radio_1
                    #self.logger.info(f"{group['frequency']}")
                
        self.ml.inject_filedict_into_miz(self.ml.miz_file,'mission', my_dict)

    def list_radios(self,filter=None):
        # List the airframes in the miz file with their groups,
        # list the radios in the config file.
        #pass
        if os.path.exists(self.conffile):
            yaml_conf = yaml.safe_load(open(self.conffile))
        else:
            yaml_conf = {}

        airframe_groups = {}
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
                        #airframes[ group['units'][1]['type'] ] = group['units'][1]["Radio"]
                        airframe_groups.setdefault(group['units'][1]['type'],[]).append(group['name'])
        print(yaml.dump({'from_yml': list(yaml_conf.keys()), 'from_miz': airframe_groups}))

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('category',choices=['radios','waypoints','payload'], help='Category of data to manage')
    # group/route/points
    parser.add_argument('action',choices=['export','import','list'],help='Action to perform')
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
    if args.category == 'radios' and args.action == 'export':
        rm.export_radios(args.filter)
    elif args.category == 'radios' and args.action == 'import':
        rm.import_radios(args.filter)
    elif args.category == 'radios' and args.action == 'list':
        rm.list_radios(args.filter)
    if args.category == 'waypoints' and args.action == 'export':
        rm.export_waypoints(args.filter)
    elif args.category == 'waypoints' and args.action == 'import':
        rm.import_waypoints(args.filter)
    else:
        print("Unknown action")
        exit(1)


