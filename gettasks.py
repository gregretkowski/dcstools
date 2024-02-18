DESCRIPTION='''
Yank task info out of bactria mission. generates a YAML file with the task info.

'''

# python gettasks.py --debug export tasks.yml '..\Saved Games\DCS\Missions\OA-Caucusus-Bactria.miz'



import argparse
import re
import logging

import yaml
import json

from mizlib import Mizlib

class GetTasks():

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


    def export_tasks(self):

        self.logger.debug("in export")
        #self.logger.debug(self.config)

        airframes = {}

        # Load mission and iterate over groups.        
        my_dict = self.ml.extract_filedict_from_miz('mission')
        dict_dict = self.ml.extract_filedict_from_miz('l10n/DEFAULT/dictionary')
        map_dict = self.ml.extract_filedict_from_miz('l10n/DEFAULT/mapResource')

        tasks = {}

        #self.logger.debug(my_dict['trigrules'].keys())
        #raise Exception("done")
        for trigrule_id, trigrule in my_dict['trigrules'].items():
            self.logger.debug(json.dumps(trigrule['comment'],indent=2))
            m = re.match(r'.*Task#(\d+)',trigrule['comment'])
            if not m:
                continue
            task_id = m.group(1)

            #if task_id != '24':
            #    continue
            self.logger.info(json.dumps(trigrule['actions'],indent=2))

            tasks[task_id] = tasks[task_id] if task_id in tasks else []
            my_task = {
                'name': trigrule['comment'],
                'actions': []
                #'triggers': []
            }



            for action_id, action in trigrule['actions'].items():
                self.logger.debug(json.dumps(action,indent=2))
                if action['predicate'] in ['a_out_sound_c', 'a_out_text_delay_c']:
                    my_action = {}
                    my_action['predicate'] = action['predicate']
                    if 'file' in action:
                       my_action['soundfile'] = map_dict[action['file']]
                    if 'text' in action:
                        my_action['text'] = dict_dict[action['text']]
                    my_task['actions'].append(my_action) 
                    

            # DO THIS LAST!
            if len(my_task['actions']) > 0:
                tasks[task_id].append(my_task)
       # raise Exception("done")

        #self.logger.info(json.dumps(tasks,indent=2))
        self.logger.info(yaml.dump(tasks))
        with open(self.conffile,'w') as f:
            f.write(yaml.dump(tasks))


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument('action',choices=['export','import'],help='Action to perform')
    parser.add_argument('conffile',help='Configuration file')
    parser.add_argument('filename')
    parser.add_argument('--debug', '-d', action='store_true', help='Enable debug logging')

    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    gt = GetTasks(args.conffile, args.filename, logger)
    if args.action == 'export':
        gt.export_tasks()
    else:
        print("Unknown action")
        exit(1)


