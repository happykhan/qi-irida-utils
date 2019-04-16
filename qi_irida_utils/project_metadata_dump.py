#!/usr/bin/env python3
import argparse
from pprint import pprint
from os import path
from api import api_calls
import sys
import yaml
import json
import re
from pathlib import Path
import pdb

# ARGUMENTS
opt_parser = argparse.ArgumentParser(description='IRIDA API command line interface to dump sample metadata as TSV')
opt_parser.add_argument('-c', '--conf', help='Path to YAML configuration file [~/.irida/uploader.yaml]', default=path.join(path.expanduser("~"), ".irida/uploader.yaml"), type=str)
opt_parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
opt_parser.add_argument('-s', '--noheaderspace', help='Replaces header spaces with underscores',  action='store_true')
opt_parser.add_argument('-z', '--novaluespace', help='Replaces spaces in cell values with underscores [!]',  action='store_true')
opt_parser.add_argument('-i', '--id', help='Project ID',required=True)

opt = opt_parser.parse_args()

#Check YAML configuration file is a file, and in YAML format
conf_file = Path(opt.conf)
if not conf_file.is_file():
    print('Configuration file not found at: ' + opt.conf)
    exit(1)
else:
    try:
        with open(opt.conf) as f:
            yaml.safe_load(f)
    except:
        print('Configuration file is not YAML (' + opt.conf + ')')
        exit(1)

# API REQUEST FUNCTION: add baseUrl and return JSON catching exceptions
def api_call(request):
    try:
        api_answer = api._session.get(api.base_url + request)
        api_json = api_answer.json()
    except Exception as ex:
        msg = [("Message","API raised exception")]
        return json.dumps(msg)

    if api_json['resource']:
        return api_json['resource']
    else:
        msg = [("Message","API answer contains no valid content")]
        return json.dumps(msg)


def jprint(json_object):
	json_object = json.dumps(json_object, indent=3, sort_keys=True)
	print(json_object)


yaml_config_file = path.join(opt.conf)
api = api_calls.initialize_api_from_config(yaml_config_file)

request = '/projects/{}/samples/'.format(opt.id)
samples = api_call(request)


def getmetadata(sample):
	request = '/samples/{}/metadata/'.format(sample);
	metadata = api_call(request)
	return metadata['metadata']



def sample_has_reads(sample, library='pairs'):
	if library!='pairs' and library!='unpaired':
		print('Coding error: function called with illegal library type (must be pairs or unpaired')
		exit(0)
	request = '/samples/{}/{}/'.format(sample, library);
	pairs = api_call(request)
	uploaded_reads = 0
	i = 0
 
	while i < len(pairs['resources']):
		if pairs['resources'][i]['processingState']=='FINISHED':
			uploaded_reads += 1;
		else:
			debug(pairs['resources'][i]['identifier']+' '+pairs['resources'][i]['label']+' '+pairs['resources'][i]['processingState'])
		i += 1
	return uploaded_reads

def sample_reads(sample):
	paired = sample_has_reads(sample, 'pairs')
	unpaired = sample_has_reads(sample, 'unpaired')
	return paired + unpaired


def debug(msg):
	if opt.verbose:
		eprint('## ' +msg)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)	


sample_table = {};
headers = {'SampleID':1, 'IRIDA_ID':1}

for sample in samples['resources']:
	id=sample['identifier']

	debug('Processing: ' + id)
	#dict_keys(['createdDate', 'modifiedDate', 'sampleName', 'description', 'organism', 'isolate', 'strain', 'collectedBy', 'collectionDate', 'geographicLocationName', 'isolationSource', 'latitude', 'longitude', 'label', 'links', 'identifier'])
	this_sample={}
	this_sample['SampleID'] = sample['sampleName']
	this_sample['IRIDA_ID'] = id
	this_sample['Description'] = sample['description']
	
	#del(this_sample['links'])
	metadata = getmetadata(sample['identifier'])
	for datum in sorted(metadata):
		headers[datum] = 1
		this_sample[datum] = metadata[datum]['value']

	uploaded_read_sets = sample_reads(id)
	this_sample['Uploaded_reads'] = uploaded_read_sets
	if uploaded_read_sets < 1:
		debug('{} has no uploaded reads'.format(sample['sampleName']))

	debug('{}\t{}\t{}'.format(id,sample['sampleName'],uploaded_read_sets))

	sample_table[id] = this_sample


# Last columns
headers['Uploaded_reads'] = 1
headers['Description'] = 1

header = ''
for column in headers:
	if opt.noheaderspace:
		column = column.replace(" ", "_")
	header += column + '\t'
print(header)

for sample in sample_table:
	line = ''
	for column in headers:
		value = sample_table[sample][column]
		if opt.novaluespace and isinstance(value, str):
			value = value.replace(" ", "_")
		line += '{}\t'.format(value)
	print(line)

