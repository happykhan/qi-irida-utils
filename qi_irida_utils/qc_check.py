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


class InitQC:
    def __init__(
        self,
        project_name,
        config_file=path.join(path.expanduser("~"), ".irida/nabil_uploader.yaml"),
    ):
        self.config_file = config_file
        self.project_name = project_name
        self.api = api_calls.initialize_api_from_config(self.config_file)

    def get_criteria(self, criteria="wgs"):
        return Wgs

    def get_projects(self, project_name):
        if self.project_name == "all":
            projects = [(x.id, x.name) for x in self.api.get_projects()]
            log.info("Running on all projects")
        else:
            projects = [
                (x.id, x.name)
                for x in self.api.get_projects()
                if x.name == project_name
            ]
        return projects

    def write_summary(self, rows):
        if len(rows) > 0:
            columns = rows[0].keys()
            write_sum = csv.DictWriter(
                open("/tmp/checksums.csv", "w"), fieldnames=columns
            )
            write_sum.writeheader()
            write_sum.writerows(rows)
        else:
            log.error("No rows in summary file")

    def merge_reads(self, project, sample_name, temp_dir):
        paired, unpaired = self.api.get_sequence_files_breakdown(project[0], sample_name)
        lanes = {}
        merged_reads_r1 = path.join(temp_dir, sample_name + '_R1.fastq')
        merged_reads_r2 = path.join(temp_dir, sample_name + '_R2.fastq')
        merged_read_exists = False
        # Check this has been done before
        for pair in paired:
            if (pair['files'][0]['label'] == 'filt.' + path.basename(merged_reads_r1)
                and pair['files'][1]['label'] == 'filt.' + path.basename(merged_reads_r2)):
                merged_read_exists = True
        if not merged_read_exists:
            if not path.exists(merged_reads_r1) or not path.exists(merged_reads_r2):
                for pair in paired:
                    if len(pair['files']) > 2:
                        log.error('More than two read files in a pair? %s' % sample_name)
                    else:
                        lane_match = re.search('.*_(L\d+)_R1_\d+.fastq.*', pair['files'][0].get('label'))
                        if lane_match:
                            lane_name = lane_match.group(1)
                            r1_filename = self.read_file_path(pair['files'][0], temp_dir, checksum=pair['files'][0]['uploadSha256'])
                            r2_filename = self.read_file_path(pair['files'][1], temp_dir, checksum=pair['files'][1]['uploadSha256'])
                            lanes[lane_name] = [r1_filename, r2_filename]
                if len(lanes) == 4:
                    subprocess.call('cat {} > {}'.format(' '.join(sorted([x[0] for x in lanes.values()])),
                                                         merged_reads_r1), shell=True)
                    subprocess.call('cat {} > {}'.format(' '.join(sorted([x[1] for x in lanes.values()])),
                                                         merged_reads_r2), shell=True)
                    temp_r1 = [x[0] for x in lanes.values() if path.dirname(x[0]) == temp_dir]
                    temp_r2 = [x[1] for x in lanes.values() if path.dirname(x[1]) == temp_dir]
                    for temp_file in (temp_r1 + temp_r2):
                        os.remove(temp_file)
                elif not merged_read_exists:
                    log.error('Reads are missing %s' % sample_name)
                    merged_read_exists = True
        return merged_reads_r1, merged_reads_r2, merged_read_exists


    def read_file_path(self, file_dict, temp_dir, checksum=None):
        # Find path to read files, or download if not found.
        seq_file_path = file_dict.get("file")
        seq_file_link = file_dict.get('links')[0].get('href')
        if not path.exists(seq_file_path):
            # Download file if it can't be seen.
            seq_file_local_path = path.join(temp_dir, path.basename(seq_file_path))
            if not path.exists(seq_file_local_path):
                self.api.download_seq_file(seq_file_link, seq_file_local_path, checksum)
            return seq_file_local_path
        else:
            return seq_file_path

    def run(self):
        # Make temp dir
        temp_dir = "/media/alikhan/4D945E8F0BE5CE8A/irida"
        if not path.exists(temp_dir):
            os.mkdir(temp_dir)
        criteria = self.get_criteria()
        for project in self.get_projects(self.project_name):
            sample_names = [x.sample_name for x in self.api.get_samples(project[0])]
            checksums = []
            log.info("Reading %d records in %s" % (len(sample_names), project[1]))
            for sample_name in sample_names:
                # first merge NextSeq reads
                r1, r2, merged = self.merge_reads(project, sample_name, temp_dir)
                if not merged:
                    # run fastp.
                    fastp_r1 = os.path.join(os.path.dirname(r1), 'filt.' + path.basename(r1))
                    fastp_r2 = os.path.join(os.path.dirname(r2), 'filt.' + path.basename(r2))
                    subprocess.call('fastp  -i {} -I {} -o {} -O {} '.format(r1, r2, fastp_r1, fastp_r2), shell=True)
                    self.api.send_sequence_files(SequenceFile([fastp_r1, fastp_r2]), sample_name, project[0], 1)


    def wait(self, sample_names, project, criteria, checksums, temp_dir):
            #
            for sample_name in sample_names:
                paired, unpaired = self.api.get_sequence_files_breakdown(project[0], sample_name)
                # Check if pairs are ok
                for pair in paired:
                    if len(pair['files']) > 2:
                        log.error('More than two read files in a pair? %s' % sample_name)
                    if pair['processingState'] != 'FINISHED':
                        log.error('Reads are not finished processing %s' % sample_name)
                    else:
                        # Look for file location on local.
                        # Build final summary dict
                        pair['files'][0].get("uploadSha256")
                        new_file = dict(
                            r1_filename=pair['files'][0].get('label'),
                            r2_filename=pair['files'][1].get('label'),
                            r1_remotepath=pair['files'][0].get('file'),
                            r2_remotepath=pair['files'][1].get('file'),
                            r1_checksum_sha256=pair['files'][0].get("uploadSha256"),
                            r2_checksum_sha256=pair['files'][1].get("uploadSha256"),
                            project_name=project[1],
                            sample_name=sample_name,
                            r1=pair[0],
                            r2=pair[1]
                        )
                        seq_file_path = pair[0].get("file")
                        seq_file_link = pair[0].get('links')[0].get('href')
                        seq_file_name = path.basename(seq_file_path.get("file"))
                        seq_file_local_path = path.join(temp_dir, seq_file_name)

                        # Generate fastp output
                        # fastp_output = seq_file_local_path + '.json'
                        # if not path.exists(fastp_output):
                        #     subprocess.call('fastp -i {} -I {} -j {}'.format(new_file['r1'], new_file['r2'],
                        #                                                      fastp_output), shell=True)
                        # fastp = json.load(open(fastp_output))
                        # new_file['q20'] = fastp['summary']['after_filtering']['q20_rate']
                        # new_file['total_reads'] = fastp['summary']['before_filtering']['total_reads']
                        # new_file['passed_reads'] = fastp['filtering_result']['passed_filter_reads']


                    if not criteria.check(new_file):
                        log.error("%s Failed QC" % new_file["sample_name"])
                    checksums.append(new_file)
                # Merge lanes if reads are good.

                print(sample_name)
            self.write_summary()


if __name__ == "__main__":
    test = InitQC("Brazil Salmonella")
    test.run()
