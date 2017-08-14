import rpyc
import sys
import glob
import pickle
import logging
from scp import SCPClient
from time import sleep
from io import BufferedReader
from pydsef import util
import copy
import datetime
import os

import paramiko as ssh
logging.getLogger("paramiko").setLevel(logging.WARNING)

conn = None
r = None
results = {}

class Experiment:
    def __init__(self, hostname, username, dist_sys, conf, port = 18861, max_retries = 10):
        self.hostname = hostname
        self.username = username
        self.dist_sys = dist_sys
        self.port = port
        self.max_retries = max_retries
        self.client = None
        self.timestamp = None
        self.archive_files = []
        self.exec_path = "run.py"
        self.conf = conf
        self.experiment_list = util.product(conf['experiment'])
        if('host' in conf): self.hosts = self.conf['host']
        else: self.hosts = None
        for i, e in enumerate(self.experiment_list):
            e.update({'id':i})
            self.experiment_list[i] = e

        # options
        self.show_log = False
        self.save_log = True

    def exec_command(self, cmd, block = True):
        if self.client == None:
            self.client = ssh.SSHClient()
            self.client.load_system_host_keys()
            self.client.set_missing_host_key_policy(ssh.WarningPolicy)
            self.client.connect(self.hostname, username = self.username)

            self.exec_command('mkdir -p dsef')

        (stdin, stdout, stderr) = self.client.exec_command("cd ~/{} && {}".format(self.dist_sys, cmd), get_pty = True)
        if block:
            return str(stdout.read(), 'ascii')
        else:
            return (stdin, stdout, stderr)

    def push_files(self, files):
        self.transfer_files(files, push = True, path = "~/{}/dsef".format(self.dist_sys))

    def pull_archives(self, files):
        pathname = self.make_timestamped_dir('archive')
        self.transfer_files(files, push = False, path = pathname + '/{f}')
        [self.exec_command('rm {}'.format(f)) for f in files]

    def write_log(self, exp_id, stdout, stderr):
        pathname = self.make_timestamped_dir('logs')
        with open('{}/{}.{}'.format(pathname, exp_id, 'out'), mode = 'wb') as f:
            f.write(stdout)

        with open('{}/{}.{}'.format(pathname, exp_id, 'err'), mode = 'wb') as f:
            f.write(stderr)

    def transfer_files(self, files, push = True, path = ""):
        if not isinstance(files, list):
            files = [files]

        def f():
            if self.client == None: self.exec_command("ls")
            with SCPClient(self.client.get_transport()) as scp:
                if push:
                    for f in sum([glob.glob(s) for s in files], []):
                        scp.put(f, remote_path = path.format(f=f))
                else:
                    for f in files:
                        scp.get("~/{}/{}".format(self.dist_sys, f), local_path = path.format(f=f))

        util.show_progress(f, 'Transfering files: {}'.format(', '.join(files)))

    def set_archive(self, *files):
        self.archive_files += files

    def make_timestamped_dir(self, name):
        s = '{}/{}'.format(name, self.timestamp)
        os.makedirs(s, exist_ok = True)
        return s

    def set_executable(self, path):
        self.exec_path = path
        self.push_files(self.exec_path)

    def run(self):
        self.connect()
        print('[+] Running {} Experiments'.format(len(self.experiment_list)))

        self.timestamp = datetime.datetime.now().strftime('%m%d%y-%H%M')
        print('[+] Timestamp: {}'.format(self.timestamp))

        for e in self.experiment_list:
            if not self.start(e): break
        return self.end()

    def connect(self):
        def f():
            self.conn = None
            i = 0
            while self.conn == None:
                try:
                    self.conn = rpyc.connect(self.hostname, self.port, config={'sync_request_timeout':60, 'allow_pickle':True})
                    break
                except ConnectionRefusedError:
                    if i >= self.max_retries:
                        print("FAIL")
                        raise ConnectionError
                    else:
                        self.server_io = self.exec_command("./dsef/{}".format(self.exec_path), block = False)
                        sleep(0.5)
                i += 1

            self.r = self.conn.root
            self.results = {}
        util.show_progress(f, 'Connecting')

    def read(self):
        stdout = b''
        while self.server_io[1].channel.recv_ready():
            stdout += self.server_io[1].read(1)

        stderr = b''
        while self.server_io[2].channel.recv_ready():
            stderr += self.server_io[2].read(1)

        return (stdout, stderr)

    def start(self, exp_dict):
        try:
            print("[+] Starting Experiment {}/{}".format(exp_dict['id'] + 1, len(self.experiment_list)))
            util.show_progress(self.r.setup, 'Setup', args = (exp_dict, self.hosts))

            util.show_progress(self.r.launch, 'Launching')

            self.results[exp_dict['id']] = copy.deepcopy(util.show_progress(self.r.run, 'Running Experiment'))

            util.show_progress(self.r.teardown, 'Tearing Down')

            (stdout, stderr) = self.read()
            if self.show_log:
                print('[+] Experiment Log:', flush = True)
                print(str(stdout, 'ascii'), file = sys.stderr, flush = True)

            if self.save_log:
                util.show_progress(self.write_log, 'Saving logs', args = (exp_dict['id'], stdout, stderr,))

        except Exception as e:
            print("[+] There was an exception while running experiment {}!!".format(exp_dict['id']))
            print(e)

            if self.server_io != None:
                self.server_io[0].close()
                self.server_io[1].close()
                self.server_io[2].close()
                print("[+] RPyC Server stdout")
                print(str(self.server_io[1].read(), 'ascii'))
                print("[+] RPyC Server stderr")
                print(str(self.server_io[2].read(), 'ascii'))

            return False

        return True

    def end(self):
        print("[+] Exiting")
        archives = copy.deepcopy(self.r.archive(*self.archive_files))
        self.pull_archives(archives)
        self.conn.close()
        self.server_io = None
        self.client.close()

        return self.results
