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
        pathname = self.make_archive_dir()
        self.transfer_files(files, push = False, path = pathname + '/{f}')
        [self.exec_command('rm {}'.format(f)) for f in files]

    def transfer_files(self, files, push = True, path = ""):
        print("[+] Transfering files: {}".format(files))

        if not isinstance(files, list):
            files = [files]

        if self.client == None: self.exec_command("ls")
        with SCPClient(self.client.get_transport()) as scp:
            if push:
                for f in sum([glob.glob(s) for s in files], []):
                    scp.put(f, remote_path = path.format(f=f))
            else:
                for f in files:
                    scp.get("~/{}/{}".format(self.dist_sys, f), local_path = path.format(f=f))

    def set_archive(self, *files):
        self.archive_files += files

    def make_archive_dir(self):
        s = 'archive/{}'.format(datetime.datetime.now().strftime('%y%m%d-%H%M'))
        os.makedirs(s, exist_ok = True)
        return s

    def set_executable(self, path):
        self.exec_path = path
        self.push_files(self.exec_path)

    def run(self):
        self.init()
        print('[+] Running {} Experiments'.format(len(self.experiment_list)))
        for e in self.experiment_list:
            if not self.start(e): break
        return self.end()

    def init(self):
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
        data = b''
        while self.server_io[1].channel.recv_ready():
            data += self.server_io[1].read(1)
        return data

    def start(self, exp_dict):
        try:
            print("[+] Starting Experiment {}/{}".format(exp_dict['id'] + 1, len(self.experiment_list)))
            util.show_progress(self.r.setup, 'Setup', args = (exp_dict, self.hosts))

            util.show_progress(self.r.launch, 'Launching')

            self.results[exp_dict['id']] = copy.deepcopy(util.show_progress(self.r.run, 'Running Experiment'))

            if self.show_log:
                print('[+] Experiment Log:')
                print(str(self.read(), 'ascii'))

            util.show_progress(self.r.teardown, 'Tearing Down')

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
