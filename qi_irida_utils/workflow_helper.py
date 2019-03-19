import urllib.request
import json
import subprocess
import os
import ssl
import logging
import xml.etree.ElementTree as ET

logging.basicConfig()
log = logging.getLogger()

### Globals ###
GALAXY_URL = "http://galaxy.quadram.ac.uk/galaxy/u/nabil/w/"
WORKFLOW_PATH = (
    "/usr/users/QIB_fr005/alikhan/code/irida/src/main/resources/ca/corefacility/bioinformatics/"
    "irida/model/workflow/analysis/type/workflows/"
)
WORKFLOW_PROP = (
    "/usr/users/QIB_fr005/alikhan/code/irida/src/main/resources/ca/corefacility/bioinformatics/"
    "irida/config/workflows.properties"
)
PIPELINES = [
    {
        "galaxy_url": GALAXY_URL + "aa2master" + "/json",
        "irida_type": "ASSEMBLY_ANNOTATION",
        "irida_name": "AssemblyAnnotation",
        "workflow_path": WORKFLOW_PATH,
    },
    {
        "galaxy_url": GALAXY_URL + "phylotypingmaster-2" + "/json",
        "irida_type": "PHYLOGENOMICS",
        "irida_name": "Phylogenetics",
        "workflow_path": WORKFLOW_PATH,
        "multiple": True,
    },
    {
        "galaxy_url": GALAXY_URL + "atat3master" + "/json",
        "irida_type": "ASSEMBLY_ANNOTATION_COLLECTION",
        "irida_name": "AssemblyAnnotationCollection",
        "workflow_path": WORKFLOW_PATH,
        "multiple": True,
    },
]

## Do things ##
# First read in config for workflows
final_config = {}
with open(WORKFLOW_PROP) as wf:
    for j in wf.readlines():
        if len(j.split("=")) == 2:
            final_config[j.split("=")[0]] = j.split("=")[1].strip()
for pipe in PIPELINES:
    # Download JSON from Galaxy
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    with urllib.request.urlopen(pipe["galaxy_url"], context=ctx) as url:
        data = json.loads(url.read().decode())
        for x, y in data["steps"].items():
            if y["label"] == "reference":
                y["tool_state"] = '{"name": "reference"}'
        with open("{irida_name}.json".format(**pipe), "w") as outfile:
            json.dump(data, outfile)
        # ALWAYS Increment version
        workflow_path = os.path.join(
            WORKFLOW_PATH,
            pipe["irida_name"])
        if os.path.exists(workflow_path):
            max_version = max([int(x.split('.')[-1]) for x in os.listdir(workflow_path)])
            pipe['irida_version'] = '0.{}'.format(max_version + 1)
        else:
            pipe['irida_version'] = '0.1'
        # Generate IRIDA files from galaxy workflow
        process_ga = (
            "java -jar lib/irida-wf-ga2xml-1.0.0-SNAPSHOT-standalone.jar "
            "-i {irida_name}.json "
            "-o {workflow_path} "
            "-W {irida_version} "
            "-t {irida_type} "
            "-n {irida_name}".format(**pipe)
        )
        if pipe.get("multiple"):
            process_ga += " --multi-sample "
        subprocess.call(process_ga, shell=True)
        # Check and clean up errors in IRIDA workflow output
        workflow_xml_path = os.path.join(
                WORKFLOW_PATH,
                pipe["irida_name"],
                pipe["irida_version"],
                "irida_workflow.xml",
            )
        workflow_xml = ET.parse(workflow_xml_path)
        workflow_root = workflow_xml.getroot()
        # CHECK XML: Tree should be names 'tree' only
        for tr_field in workflow_root.iterfind('outputs/output'):
            if tr_field.get('fileName') == 'tree.newick':
                tr_field.set('name', 'tree')
        # CHECK XML: has sequence Reads Paired specified
        for sq_field in workflow_root.iterfind('inputs/sequenceReadsPaired'):
            sq_field.text = 'sequence_reads_paired'
        # CHECK XML: Get workflow ID
        for id_field in workflow_root.iterfind('id'):
            final_config["irida.workflow.default.{}".format(pipe["irida_type"])] = id_field.text
        # Write XML
        workflow_xml.write(open(workflow_xml_path, 'w'), encoding='unicode')
        # CHECK JSON: Make sure galaxy json has the name specified.
        ga_json = os.path.join(
            WORKFLOW_PATH,
            pipe["irida_name"],
            pipe["irida_version"],
            "irida_workflow_structure.ga",
        )
        x = json.load(open(ga_json))
        # CHECK JSON: Make sure input labels are specified
        input_exists = False
        for step_num, step in x['steps'].items():
            if step.get('label') == 'sequence_reads_paired':
                if len(step['inputs']) < 1 or not step['inputs'][0].get('name'):
                    log.warning('inputs field for input reads not specified')
                step['inputs'] = [dict(description="", name="sequence_reads_paired")]
                input_exists = True
        # CHECK JSON: Make sure inputs are specified
        if not input_exists:
            log.exception('Read input is not specified correctly. No sequence_read_paired component found')
        with open(ga_json, "w") as ga_file:
            ga_file.write(json.dumps(x, indent=4, sort_keys=True))


# Finally reformat workflow config, to have new hashes for the updated pipelines
with open(WORKFLOW_PROP, "w") as wf:
    for k, v in final_config.items():
        wf.write("{}={}\n".format(k, v))
