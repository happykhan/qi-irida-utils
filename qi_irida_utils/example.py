from os import path
from api import api_calls

config_file = path.join(path.expanduser("~"), ".irida/nabil_uploader.yaml")
api = api_calls.initialize_api_from_config(config_file)

x = api._session.get(
    "http://db.informatics.quadram.ac.uk:8080/irida/api/samples/1045/metadata"
)
from pprint import pprint

print(pprint(x.json()))
