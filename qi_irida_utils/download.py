from api import api_calls
from os import path


def get_project_id(project_name):
    return [x.id for x in api.get_projects() if x.name == project_name]


def get_sample_files(project_id):
    api.get_samples()


api = api_calls.initialize_api_from_config(path.join(path.expanduser("~"), ".irida/nabil_uploader.yaml"))
get_project_id('STEC_nabil')
