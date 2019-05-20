from api import api_calls
from os import path
import os

class CheckAssembly:
    '''
    Check an IRIDA sample sheet file against the content in IRIDA. Is sample present?
    Does sample have reads? Does sample have assembly?
    '''
    def __init__(
        self,
        project_name,
        manifest,
        public_data=None,
        delete=False,
        config_file=path.join(path.expanduser("~"), ".irida/nabil_uploader.yaml"),
    ):
        self.config_file = config_file
        self.project_name = project_name
        self.api = api_calls.initialize_api_from_config(self.config_file)
        self.manifest = manifest
        self.public_data = public_data
        self.public_data_meta = public_data_meta
        self.delete = False

    def _get_manifest_samples(self):
        with open(self.manifest) as f:
            return [mani_line.split(',')[0].strip() for mani_line in f.readlines()[2:]]

    def clean_failed_assemblies(self, project_id):
        for sample in self.api.get_samples(project_id):
            # Check samples for some read pairs [sample/sequenceFiles/pairs]
            paired_link = [x['href'] for x in sample['links'] if x['rel'] == 'sample/sequenceFiles/pairs'][0]
            read_pairs = self.api._session.get(paired_link)
            read_pair_list = read_pairs.json()['resource']['resources'] # List of read pairs (each json)
            # Delete any read pairs that failed to assemble.
            for read_pair in read_pair_list:
                assembly_job_list = [x['href'] for x in read_pair_list[0]['links'] if x['rel'] == 'analysis/assembly']
                if assembly_job_list:
                    assembly_obj = self.api._session.get(assembly_job_list[0]).json()['resource']
                    if assembly_obj['analysisState'] == 'ERROR':
                        delete_list = []
                        for link in delete_list:
                            self.api._session.delete(link['href'])


    def run(self):
        # Get manifest
        samples = self._get_manifest_samples()
        if self.public_data:
            public_samples = self.public_genomes_dict()
        irida_samples = []
        project_id = [x.id for x in self.api.get_projects() if x.name == self.project_name][0]
        if self.delete:
            # Delete any read pairs that failed to assemble.
            self.clean_failed_assemblies(project_id)

        # Get all samples from project
        for sample in self.api.get_samples(project_id):
            # Check samples for some read pairs [sample/sequenceFiles/pairs]
            paired_link = [x['href'] for x in sample['links'] if x['rel'] == 'sample/sequenceFiles/pairs'][0]
            read_pairs = self.api._session.get(paired_link)
            read_pair_list = read_pairs.json()['resource']['resources']
            if len(read_pair_list) >= 1:
                irida_samples.append(sample.sample_name.strip())
                raw_read_info = read_pair_list[0]['files']
                # From sequencing pair, check if assembly is attached
                assembly_job_list = [x['href'] for x in read_pair_list[0]['links'] if x['rel'] == 'analysis/assembly']
                if assembly_job_list:
                    assembly_status = self.api._session.get(assembly_job_list[0]).json()['resource']['analysisState']
                    # Pull some output

                else:
                    assembly_status = 'NOJOB*'
                print(sample.sample_name + '\t' + assembly_status)


            if len(read_pair_list) > 1:
                print(sample.sample_name + '\t' + 'MULTIPLE*')

        # Are samples in missing from project
        no_read_samples = list(set(samples) - set(irida_samples))
        if self.public_data:
            no_read_public = list(set(public_samples.values()) - set(irida_samples))
        read_dir = os.path.dirname(self.manifest)
        basespace_path = "/usr/users/QIB_fr005/alikhan/seq/Projects/Emma_D/Samples"
        new_sample = open(read_dir + '/SampleList.csv', 'w')
        new_sample.write('[Data]\n')
        new_sample.write('Sample_Name,Project_ID,File_Forward,File_Reverse\n')
        #/usr/users/QIB_fr005/alikhan/seq/Projects/Emma_D/Samples/PID0023_Chicken_2_C06/Files
        with open(self.manifest) as f:
            for sample in f.readlines()[2:]:
                sample_name = sample.strip().split(',')[0]
                if sample_name in no_read_samples:
                    if len(sample.split(',')) < 2:
                        r1_path, r2_path = self.do_cat(sample_name, basespace_path, read_dir)
                        new_sample.write(sample_name + '\t53\t' + os.path.basename(r1_path)
                                         + ',' + os.path.basename(r2_path) + '\n')
        if self.public_data:
            public_samples = self.public_genomes_dict()
            self.download_sra(public_samples, read_dir, no_read_public, new_sample, ascp=False)

    @staticmethod
    def do_cat(sample_name, ori_path, outpath):
        read_path = ori_path + '/' + sample_name + '/Files'
        r1 = sorted([read_path + '/' + x for x in os.listdir(read_path) if x.endswith('R1_001.fastq.gz')])
        r2 = sorted([read_path + '/' + x for x in os.listdir(read_path) if x.endswith('R2_001.fastq.gz')])
        r1_out = os.path.join(outpath, sample_name + '_R1.fastq.gz')
        r2_out = os.path.join(outpath, sample_name + '_R2.fastq.gz')
        if not os.path.exists(r1_out):
            cat_command  = 'cat %s > %s '  %(' '.join(r1), r1_out )
            print(cat_command)
            # subprocess.call(cat_command), shell=True)
        if not os.path.exists(r2_out):
            cat_command = 'cat %s > %s ' % (' '.join(r2), r2_out )
            print(cat_command)
            # subprocess.call(cat_command, shell=True)
        return r1_out, r2_out

    def public_genomes_dict(self):
        meta = {}
        with open(self.public_data) as md:
            for mdline in md.readlines():
                meta[mdline.strip()] = mdline.strip()
        if self.public_data_meta:
            meta_file = self.public_data_meta
            with open(meta_file) as md:
                for mdline in md.readlines()[1:]:
                    acc = mdline.split('\t')[2].split(';')[0]
                    name = mdline.split('\t')[1]
                    if meta.get(acc):
                        meta[acc] = name
        return meta

    @staticmethod
    def download_sra(file_dict, download_dir, no_read_public, new_sample, ascp=False):
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        write_file = open(os.path.join(download_dir, 'get_data.sh'), 'w')
        for accession, sample_name in file_dict.items():
            fastq_1_file = os.path.join(download_dir, "{}_1.fastq.gz".format(sample_name))
            fastq_2_file = os.path.join(download_dir, "{}_2.fastq.gz".format(sample_name))
            path = 'sra/sra-instant/reads/ByRun/sra/{}/{}/{}/{}.sra'.format(accession[0:3], accession[0:6],
                                                                             accession, accession,)
            if ascp:
                x = "/usr/users/QIB_fr005/alikhan/.aspera/connect/bin/ascp " \
                    "-i ~/.aspera/connect/etc/asperaweb_id_dsa.openssh " \
                    "-T " \
                    "-k 1 " \
                    "anonftp@ftp.ncbi.nlm.nih.gov:/{}" \
                    " {} ".format(path, download_dir)
                x = x + "\nfasterq-dump {}.sra -o {}".format(accession, sample_name )
            else:
                x = "fasterq-dump -v {} -o {}".format(accession, sample_name)
            if not os.path.exists(fastq_1_file) and sample_name in no_read_public:
                write_file.write('%s\n' % x)
                x = "gzip {}_1.fastq".format(sample_name)
                write_file.write('%s\n' % x)
                x = "gzip {}_2.fastq".format(sample_name)
                write_file.write('%s\n' % x)
            if os.path.exists(fastq_1_file) and os.path.exists(fastq_2_file) and sample_name in no_read_public:
                new_sample.write(sample_name + ',53,' + "{}_1.fastq.gz".format(sample_name)
                                 + ',' + "{}_2.fastq.gz".format(sample_name) + '\n')

if __name__ == "__main__":
    manifest = '/media/alikhan/4D945E8F0BE5CE8A/braz/uploaded.csv'
    public_data_meta = '/media/alikhan/4D945E8F0BE5CE8A/braz/public_data.tsv'
    public_data = '/usr/users/QIB_fr005/alikhan/work/labbook/public_acc.tsv'
    test = CheckAssembly("B_Sal Complete", manifest, public_data, public_data_meta)
    test.run()
