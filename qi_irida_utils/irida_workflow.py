import subprocess
import os
import csv
from multiprocessing import Manager, Process, Queue
import logging
from subprocess import call
import copy

log = logging.getLogger()


class FetchReads:
    def __init__(
        self,
        Sample_name,
        Accession,
        File_Forward,
        File_Reverse,
        aspera_path,
        aspera_key,
        output_dir,
        fastq_dump_path,
        Project_ID,
    ):
        self.acc = Accession
        self.sample_name = Sample_name
        self.aspera_path = aspera_path
        self.aspera_key = aspera_key
        self.output_dir = output_dir
        self.fastq_dump_path = fastq_dump_path
        self.r1 = File_Forward
        self.r2 = File_Reverse
        self.project_id = Project_ID

    def run(self):
        if self.acc:
            if not os.path.exists(self.output_dir):
                os.mkdir(self.output_dir)
            ascp_command = [
                os.path.join(self.aspera_path, "ascp"),
                "-i",
                self.aspera_key,
                "-k",
                "1",
                "-T",
                "-l200m",
            ]
            ftp_path = "anonftp@ftp.ncbi.nlm.nih.gov:/sra/sra-instant/reads/ByRun/sra/{:.3}/{:.6}/{}/{}.sra".format(
                self.acc, self.acc, self.acc, self.acc
            )
            ascp_command += [ftp_path, self.output_dir]
            if not os.path.exists(os.path.join(self.output_dir, self.acc + ".sra")):
                log.debug("Running " + " ".join(ascp_command))
                subprocess.call(ascp_command)
            fastq_dump_command = [
                os.path.join(self.fastq_dump_path, "fastq-dump"),
                "--gzip",
                "--split-files",
                os.path.join(self.output_dir, self.acc + ".sra"),
                "--outdir",
                os.path.join(self.output_dir),
            ]
            self.r1 = os.path.join(self.output_dir, self.acc + "_1.fastq.gz")
            self.r2 = os.path.join(self.output_dir, self.acc + "_2.fastq.gz")
            if not os.path.exists(self.r1):
                log.debug("Running " + " ".join(fastq_dump_command))
                subprocess.call(fastq_dump_command)
        if os.path.exists(self.r1) and os.path.exists(self.r2):
            log.info("Downloaded {}".format(self.sample_name))
            irida_sample_file = os.path.join(
                self.output_dir, "SampleList.csv"
            )
            with open(irida_sample_file, "w") as temp_sheet:
                temp_sheet.write("[Data]\n")
                temp_sheet.write("Sample_Name,Project_ID,File_Forward,File_Reverse\n")
                temp_sheet.write(
                    "{},{},{},{}\n".format(
                        self.sample_name,
                        self.project_id,
                        os.path.basename(self.r1),
                        os.path.basename(self.r2),
                    )
                )
                temp_sheet.close()
                log.info("Uploading {} to IRIDA".format(self.sample_name))
                call(
                    [
                        "python",
                        "../irida-uploader/upload_run.py",
                        "-c",
                        "config.conf",
                        self.output_dir,
                    ]
                )
        else:
            log.info("File could not be found {}".format(self.r1))


def worker(q):
    while True:
        obj = q.get()
        obj.run()
        if q.empty():
            break


def prepare_sample(
    sample_file, aspera_path, aspera_key, fastq_dump_path, output_dir, num_workers=2
):
    upload_queue = Queue()
    workers = []
    for x in range(num_workers):
        upload_proc = Process(target=worker, args=(upload_queue,))
        upload_proc.start()
        workers.append(upload_proc)
    config = dict(
        aspera_path=aspera_path,
        aspera_key=aspera_key,
        fastq_dump_path=fastq_dump_path,
        output_dir=output_dir,
    )
    # Try to finish off read files already saved locally.
    for x in sorted(
        [x for x in csv.DictReader(open(sample_file))],
        key=lambda i: i["File_Forward"],
        reverse=True,
    ):
        if x.get("Sample_name"):
            if x.get("Accession"):
                y = copy.deepcopy(config)
                y.update(x)
                y['output_dir'] = os.path.join(y['output_dir'], y['Sample_name'])
                upload_queue.put(FetchReads(**y))
                log.debug("Queued sra: {}".format(x.get("Sample_name")))
            else:
                log.warning(
                    "Sample {} does not have enough input, skipping".format(
                        x.get("Sample_name")
                    )
                )
        else:
            log.warning("Sample has no name, skipping")
    log.info("{} Samples Queued.".format(upload_queue.qsize()))
    for x in workers:
        x.join()
    log.info("Samples uploaded.")
