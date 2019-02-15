import subprocess
import os
import csv
from multiprocessing import Process, Queue
import logging
from subprocess import Popen
import copy
import shutil
import time

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
        if not os.path.exists(self.output_dir):
            os.mkdir(self.output_dir)
        if self.acc:
            self.r1 = os.path.join(self.output_dir, self.acc + "_1.fastq.gz")
            self.r2 = os.path.join(self.output_dir, self.acc + "_2.fastq.gz")
            if True:
                # if os.path.exists(self.r1):
                log.debug("Exists, skipping " + self.r1)
            else:
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
                sra_file = os.path.join(self.output_dir, self.acc + ".sra")
                if not os.path.exists(sra_file):
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
                log.debug("Running " + " ".join(fastq_dump_command))
                subprocess.call(fastq_dump_command)
                log.info("Downloaded {}".format(self.sample_name))
                os.remove(sra_file)
        else:
            # Handling local files
            ori_r1 = self.r1
            ori_r2 = self.r2
            self.r1 = os.path.join(self.output_dir, self.sample_name + "_1.fastq.gz")
            self.r2 = os.path.join(self.output_dir, self.sample_name + "_2.fastq.gz")
            log.info("Copying {}".format(self.sample_name))
            if not os.path.exists(self.r1):
                shutil.copy(ori_r1, self.r1)
            if not os.path.exists(self.r2):
                shutil.copy(ori_r2, self.r2)
        return dict(
            sample_name=self.sample_name,
            project_id=self.project_id,
            r1=self.r1,
            r2=self.r2,
        )


def worker(q, output_queue):
    while True:
        obj = q.get()
        output_queue.put(obj.run())
        if q.empty():
            log.info("spanner {}".format(q.qsize()))
            break


def prepare_sample(
    sample_file, aspera_path, aspera_key, fastq_dump_path, output_dir, num_workers=2
):
    upload_queue = Queue()
    output_queue = Queue()
    workers = []
    for x in range(num_workers):
        upload_proc = Process(target=worker, args=(upload_queue, output_queue))
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
            if x.get("Accession") or (x.get("File_Forward") and x.get("File_Reverse")):
                y = copy.deepcopy(config)
                y.update(x)
                upload_queue.put(FetchReads(**y))
                log.debug("Queued: {}".format(x.get("Sample_name")))
            else:
                log.warning(
                    "Sample {} does not have enough input, skipping".format(
                        x.get("Sample_name")
                    )
                )
        else:
            log.warning("Sample has no name, skipping")
    log.info("{} Samples Queued.".format(upload_queue.qsize()))
    time.sleep(1)
    for x in workers:
        x.join()
    log.info("Read files ready!")
    all_results = [output_queue.get() for x in workers]
    upload_irida(all_results, output_dir)
    log.info("Samples uploaded.")


def upload_irida(all_results, output_dir):
    irida_sample_file = os.path.join(output_dir, "SampleList.csv")
    with open(irida_sample_file, "w") as temp_sheet:
        temp_sheet.write("[Data]\n")
        temp_sheet.write("Sample_Name,Project_ID,File_Forward,File_Reverse\n")
        for res in all_results:
            if os.path.exists(res["r1"]) and os.path.exists(res["r2"]):
                temp_sheet.write(
                    "{},{},{},{}\n".format(
                        res["sample_name"],
                        res["project_id"],
                        os.path.basename(res["r1"]),
                        os.path.basename(res["r2"]),
                    )
                )
            else:
                log.error(" Path {} or {} do not exist ".format(res["r1"], res["r2"]))
        temp_sheet.close()
        log.info("Uploading to IRIDA")
        stderr = b"ERROR"
        count = 1
        while "ERROR" in stderr.decode("utf-8"):
            if count > 1:
                log.warning("{}".format(stderr))
                time.sleep(1)
            log.info("Uploading  to IRIDA attempt {}".format(count))
            p = Popen(
                [
                    "python",
                    "/usr/users/QIB_fr005/alikhan/code/irida-uploader/upload_run.py",
                    "-c",
                    "/usr/users/QIB_fr005/alikhan/code/qi_irida_utils/config.conf",
                    output_dir,
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            stdout, stderr = p.communicate()
            count += 1
