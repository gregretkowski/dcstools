import yaml
# import dcs
from zipfile import ZipFile
from slpp import slpp as lua
import six
import shutil
import os
import json
import sys
import tempfile
import logging



class Mizlib():

    MIZ_FILE='Syria_Training.miz'
    RELEASE='devel'

    def __init__(self,miz_file,release=None, logger=None):
        self.base = self.filebase(miz_file)
        self.miz_file = miz_file

        if release is not None:
            self.release = release
        else:
            self.release = 'devel'

        if logger is not None:
            self.logger = logger
        else:
            logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
            self.logger = logging.getLogger(__name__)

        self.config = None
        # Note to self -- this is for weather thingie!
        # update scripts to load it later.


    def load_wx_config(self):
        with open('pyscripts/missions.yml') as f:
            self.config = yaml.safe_load(f)


    # Takes two dictionaries. will take the values from the second and merge/overwrite the first 
    def deep_merge(self, dict1, dict2):
        result = dict1.copy()

        for key, value in dict2.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge dictionaries for nested keys
                
                result[key] = self.deep_merge(result[key], value)
            else:
                # Non-dictionary values or new keys
                
                self.logger.debug("merge repleace key %s value %s with %s" % (key, result.get('key',None), value))
                #print(f"merge replace key {key} value {result[key]} with {value}")
                result[key] = value

        return result

    # Remove files from a zip. inefficient but must be done as there is
    # no 'replace' file in a zip option for python zipfile
    @classmethod
    def remove_from_zip(cls, zipfname, *filenames):
        # print(filenames)
        tempdir = tempfile.mkdtemp()
        try:
            tempname = os.path.join(tempdir, 'new.zip')
            with ZipFile(zipfname, 'r') as zipread:
                with ZipFile(tempname, 'w') as zipwrite:
                    for item in zipread.infolist():
                        if item.filename not in filenames:
                            data = zipread.read(item.filename)
                            zipwrite.writestr(item, data)
            shutil.move(tempname, zipfname)
        finally:
            shutil.rmtree(tempdir)


    def get_file_from_zip(cls,filename):
        pass

    def filebase(self,filename):
            file_basename, _ = os.path.splitext(os.path.basename(filename))
            return file_basename

    def extract_filedict_from_miz(self, filename):
        file_string = self.extract_filestring_from_miz(filename)
        base_obj = os.path.basename(filename)
        # Manipulate the strings
        dictionary = lua.decode("{" + file_string + "}")
        return dictionary[base_obj]
    
    def inject_filedict_into_miz(self, miz_filename, filename, dictionary):
        base_obj = os.path.basename(filename)
        self.remove_from_zip(miz_filename, filename)
        with ZipFile(miz_filename, 'a') as myzip:
            dictionary_string = f"{base_obj} = " + lua.encode(dictionary)
            myzip.writestr(filename,dictionary_string)
                #mission_string = "mission = " + lua.encode(mission['mission'])
                #myzip.writestr('mission',mission_string)


    def extract_filestring_from_miz(self, filename):
        # Just go get the mission file from the zip, and put it in current dir.
        with ZipFile(self.miz_file) as myzip:
                with myzip.open(filename) as mizfile:
                    file_string = mizfile.read().decode("utf-8")
        return file_string
    

    def extract_miztxt(self):
        self.base
        self.miz_file
        extracted_filename = f"mission.{self.base}.txt"

        file_string = self.extract_filestring_from_miz(self,'mission')
        with open(extracted_filename, 'wb') as outfile:
            outfile.write(file_string)
        self.logger.info('Wrote miz file to %s' % extracted_filename)



    
    def doit(self,outdir='.'):

        for key,val in self.config.items():
            file_basename = self.filebase(self.miz_file)

            new_filename = outdir + '/' + file_basename + "_" + key + ".miz"
            self.logger.info("Creating New MIZ file %s" % new_filename)
            shutil.copy2(self.miz_file, new_filename)

            # Pull out the 'dictionary' and the 'mission'
            dictionary_string = None
            mission_string = None
            with ZipFile(new_filename) as myzip:
                with myzip.open('l10n/DEFAULT/dictionary') as dictfile:
                    dictionary_string = dictfile.read().decode("utf-8")
                with myzip.open('mission') as mizfile:
                    #print(myfile.read())
                    mission_string = mizfile.read().decode("utf-8")

            # Manipulate the strings
            dictionary = lua.decode("{" + dictionary_string + "}")
            miz_deets = f"{file_basename} {key} {self.release}\\\n"
            dictionary['dictionary']["DictKey_descriptionText_1"] = miz_deets + dictionary['dictionary']["DictKey_descriptionText_1"]
            mission = lua.decode("{" + mission_string + "}")
            #print(json.dumps(mission,indent=4))
            mission['mission'] = self.deep_merge(mission['mission'],val)
            #print(json.dumps(dictionary,indent=4))
            #sys.exit

            # Pump them back into the .miz
            self.remove_from_zip(new_filename, 'mission','l10n/DEFAULT/dictionary')
            with ZipFile(new_filename, 'a') as myzip:
                dictionary_string = "dictionary = " + lua.encode(dictionary['dictionary'])
                myzip.writestr('l10n/DEFAULT/dictionary',dictionary_string)
                mission_string = "mission = " + lua.encode(mission['mission'])
                myzip.writestr('mission',mission_string)
        


