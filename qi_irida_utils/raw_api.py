#!/usr/bin/env python3
import argparse
from pprint import pprint
from os import path
from api import api_calls
import yaml
import json
from pathlib import Path


# ARGUMENTS
# NOTE If using -v (verbose) will break the JSON output
# To get a file to read: type=argparse.FileType('r')

opt_parser = argparse.ArgumentParser(description='IRIDA API command line interface. Try with "/users/" as request')
opt_parser.add_argument('request', help='REST API request (without base URL)', default='/users/')
opt_parser.add_argument('-c', '--conf', help='Path to YAML configuration file [~/.irida/uploader.yaml]', default=path.join(path.expanduser("~"), ".irida/uploader.yaml"), type=str)
opt_parser.add_argument('-v', '--verbose', help='Increase output verbosity', action='store_true')
opt_parser.add_argument('-n', '--nopretty', help='Disable JSON pretty print', action='store_true')
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


# Add verbose info (TODO: avoid breaking JSON in case of success, at the moment to strip # lines in the output)
if opt.verbose:
    print('#Conf:    ' + opt.conf)
    print('#Request: ' + opt.request)

yaml_config_file = path.join(opt.conf)
api = api_calls.initialize_api_from_config(yaml_config_file)
answer = api_call(opt.request)

if opt.nopretty==False:
  answer = json.dumps(answer, indent=3, sort_keys=True)

print(answer)

