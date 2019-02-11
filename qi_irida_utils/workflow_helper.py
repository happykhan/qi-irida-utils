import urllib.request
import json
import re
import subprocess
import os
import ssl

### Globals ###
GALAXY_URL = 'http://galaxy.quadram.ac.uk/galaxy/u/nabil/w/'
WORKFLOW_PATH = '/usr/users/QIB_fr005/alikhan/code/irida/src/main/resources/ca/corefacility/bioinformatics/' \
                'irida/model/workflow/analysis/type/workflows/'
WORKFLOW_PROP = '/usr/users/QIB_fr005/alikhan/code/irida/src/main/resources/ca/corefacility/bioinformatics/' \
                'irida/config/workflows.properties'
PIPELINES = [{
    'galaxy_url': GALAXY_URL + 'assemblyannotation-2' + '/json',
    'irida_type': 'ASSEMBLY_ANNOTATION',
    'irida_name': 'AssemblyAnnotation',
    'irida_version': '0.7.3',
    'workflow_path': WORKFLOW_PATH,
    'uuid': '4ab671c3-ebfb-4cae-82a6-2facb3d09f23'
    },
    {
        'galaxy_url': GALAXY_URL + 'phylogeneticsmaster' + '/json',
        'irida_type': 'PHYLOGENOMICS',
        'irida_name': 'Phylogenetics',
        'irida_version': '0.1',
        'workflow_path': WORKFLOW_PATH,
        'multiple': True,
        'uuid': '4b6685e3-db29-4064-9364-409bed00ea05'
    },
]

## Do a thing ##
# First read in config for workflows
final_config = {}
with open(WORKFLOW_PROP) as wf:
    for j in wf.readlines():
        if len(j.split('=')) == 2:
            final_config[j.split('=')[0]] = j.split('=')[1].strip()
for pipe in PIPELINES:
    # Download JSON from Galaxy
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(pipe['galaxy_url'], context=ctx) as url:
        data = json.loads(url.read().decode())
        for x, y in data['steps'].items():
            if y['label'] == 'reference':
                y['tool_state'] = "{\"name\": \"reference\"}"
        with open('{irida_name}.json'.format(**pipe), 'w') as outfile:
            json.dump(data, outfile)
        # Generate IRIDA files from galaxy workflow
        process_ga = 'java -jar lib/irida-wf-ga2xml-1.0.0-SNAPSHOT-standalone.jar ' \
                     '-i {irida_name}.json ' \
                     '-o {workflow_path} ' \
                     '-W {irida_version} ' \
                     '-t {irida_type} ' \
                     '-n {irida_name}'.format(**pipe)
        if pipe.get('multiple'):
            process_ga += ' --multi-sample '
        subprocess.call(process_ga, shell=True)
        with open(os.path.join(WORKFLOW_PATH, pipe['irida_name'], pipe['irida_version'], 'irida_workflow.xml')) \
                as wf:
            for x in wf.readlines():
                for match in re.finditer(r'<id>(.+)<\/id>', x):
                    final_config['irida.workflow.default.{}'.format(pipe['irida_type'])] = match.group(1)
        # Make sure galaxy json has the name specified.
        x = json.load(open(os.path.join(WORKFLOW_PATH, pipe['irida_name'], pipe['irida_version'],
                                        'irida_workflow_structure.ga')))
        # Remove _master from galaxy .ga file




# Finally reformat workflow config, to have new hashes for the updated pipelines
with open(WORKFLOW_PROP, 'w') as wf:
    for k, v in final_config.items():
        wf.write('{}={}\n'.format(k, v))

