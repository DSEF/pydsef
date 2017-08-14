import rpyc
from rpyc.utils.server import ThreadedServer
import copy
import inspect
import shutil
import os

class Registry:
    connect_list = []
    disconnect_list = []
    setup_list = []
    launch_list = []
    run_fun = None
    teardown_list = []

    server = None

    @staticmethod
    def connect(fun):
        Registry.connect_list.append(fun)
        return fun

    @staticmethod
    def disconnect(fun):
        Registry.disconnect_list.append(fun)
        return fun

    @staticmethod
    def setup(fun):
        Registry.setup_list.append(fun)
        return fun

    @staticmethod
    def launch(fun):
        Registry.launch_list.append(fun)
        return fun

    @staticmethod
    def run(fun):
        if Registry.run_fun == None:
            Registry.run_fun = fun
        else:
            raise Exception
        return fun

    @staticmethod
    def teardown(fun):
        Registry.teardown_list.append(fun)
        return fun

    @staticmethod
    def experiment(cls, port = 18861):
        def archive(self, *filenames):
            output = []
            for fn in filenames:
                output.append(shutil.make_archive(fn, 'gztar', base_dir=fn))
            return output

        cls.exposed_archive = archive
        server = ThreadedServer(cls, port = port, protocol_config = {'allow_pickle':True})
        print("Starting RPyC Server...")
        server.start()
        return cls

class Service(rpyc.Service):
    def on_connect(self, *args, **kwargs):
        for f in Registry.connect_list:
            f(self, *args, **kwargs)

    def on_disconnect(self, *args, **kwargs):
        for f in Registry.disconnect_list:
            f(self, *args, **kwargs)

    def exposed_setup(self, exp_dict, conf):
        exp_dict = copy.deepcopy(exp_dict)
        conf = copy.deepcopy(conf)
        for f in Registry.setup_list:
            f(self, exp_dict, conf)

    def exposed_launch(self, *args, **kwargs):
        for f in Registry.launch_list:
            f(self, *args, **kwargs)

    def exposed_run(self, *args, **kwargs):
        return Registry.run_fun(self, *args, **kwargs)

    def exposed_teardown(self, *args, **kwargs):
        for f in Registry.teardown_list:
            f(self, *args, **kwargs)
