import os

def download_sra(file_list, download_dir, metadata=None, ascp=False):
    with open(file_list) as f:
        if not os.path.exists(download_dir):
            os.mkdir(download_dir)
        write_file = open(os.path.join(download_dir, 'get_data.sh'), 'w')
        sample_sheet = open(os.path.join(download_dir, 'SampleList.csv'), 'w')
        sample_sheet.write('[Data]\n')
        sample_sheet.write('Sample_Name\tProject_ID\tFile_Forward\tFile_Reverse\n')
        meta = {}
        if metadata:
            with open(metadata) as md:
                for mdline in md.readlines()[1:]:
                    acc = mdline.split('\t')[2].split(';')[0]
                    name = mdline.split('\t')[1]
                    meta[acc] = name
        for line in f.readlines():
            accession = line.strip()
            sample_name = meta.get(accession, accession)
            fastq_1_file = os.path.join(download_dir, "{}_1.fastq".format(sample_name))
            fastq_2_file = os.path.join(download_dir, "{}_2.fastq".format(sample_name))
            path = 'sra/sra-instant/reads/ByRun/sra/{}/{}/{}/{}.sra'.format(accession[0:3], accession[0:6],
                                                                             accession, accession,)
            if ascp:
                x = "/usr/users/QIB_fr005/alikhan/.aspera/connect/bin/ascp " \
                    "-i ~/.aspera/connect/etc/asperaweb_id_dsa.openssh " \
                    "-T " \
                    "-k 1 " \
                    "anonftp@ftp.ncbi.nlm.nih.gov:/{}" \
                    " {} ".format(path, download_dir)
            else:
                x = "fasterq-dump -v {} -o {}".format(accession, sample_name)
            if not os.path.exists(fastq_1_file):
                write_file.write('%s\n' % x)
                x = "fasterq-dump {}.sra -o {}".format(accession, sample_name )
                write_file.write('%s\n' % x)
            sample_sheet.write('{}\t{}\t{}\t{}\n'.format(sample_name,
                                                         "53",
                                                         os.path.basename(fastq_1_file),
                                                         os.path.basename(fastq_2_file)))

download_sra('/media/alikhan/4D945E8F0BE5CE8A/SRA_public_data',
             '/media/alikhan/4D945E8F0BE5CE8A/sra_ref',
             '/media/alikhan/4D945E8F0BE5CE8A/sra_ref/phe_data.tsv')

