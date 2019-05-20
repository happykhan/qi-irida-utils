from api import api_calls
from os import path
import csv
import logging
import os
import subprocess
import re
from model.sequence_file import SequenceFile
import json
from quality.wgs import Wgs

logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.DEBUG)


class InitMergeOK:
    def __init__(
        self,
        config_file=path.join(path.expanduser("~"), ".irida/nabil_uploader.yaml"),
    ):
        self.config_file = config_file
        self.project_name = "Basespace-Emma_D"
        self.api = api_calls.initialize_api_from_config(self.config_file)

    def get_projects(self, project_name):
        if self.project_name == "all":
            projects = [(x.id, x.name) for x in self.api.get_projects() if x.name.starswith('Basespace-')]
            log.info("Running on all projects")
        else:
            projects = [
                (x.id, x.name)
                for x in self.api.get_projects()
                if x.name == project_name
            ]
        return projects

    def run(self):
        for project in self.get_projects(self.project_name):
            sample_names = [x.sample_name for x in self.api.get_samples(project[0])]
            log.info("Reading %d records in %s" % (len(sample_names), project[1]))
            for sample_name in sample_names:
                # first merge NextSeq reads
                paired, unpaired = self.api.get_sequence_files_breakdown(project[0], sample_name)
                merged_reads_r1 = 'filt.' + sample_name + '_R1.fastq'
                merged_reads_r2 = 'filt.' + sample_name + '_R2.fastq'
                merged_read_exists = False
                r1_list = [pair['files'][0]['label'] for pair in paired if pair.get('processingState') == 'FINISHED']
                r2_list = [pair['files'][1]['label'] for pair in paired if pair.get('processingState') == 'FINISHED']
                if merged_reads_r1 in r1_list and merged_reads_r2 in r2_list:
                            merged_read_exists = True
                if merged_read_exists:
                    for pair in paired:
                        read_name = pair.get('files')[0].get('label')
                        lane_match = re.search('.*_(L\d+)_R[12]_\d+.fastq.*', read_name)
                        if lane_match:
                            for read in pair.get('files'):
                                file_path = read.get('file')
                                print(file_path)
                            delete_this = pair.get('links')[0].get('href')
                            self.api._session.delete(delete_this)


if __name__ == "__main__":
    test = InitMergeOK()
    test.run()
