import rpyc
from rpyc.utils.server import ThreadedServer

def experiment(cls, port = 18861):
    t = ThreadedServer(cls, port = port, protocol_config = {'allow_pickle':True})
    print("Starting RPyC Server...")
    t.start()

class Registry:
    connect_list = []
    disconnect_list = []
    setup_list = []
    launch_list = []
    run_list = []
    teardown_list = []

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
        Registry.run_list.append(fun)
        return fun

    @staticmethod
    def teardown(fun):
        Registry.teardown_list.append(fun)
        return fun

class Service(rpyc.Service):
    def on_connect(self):
        for f in Registry.connect_list:
            f(self, *args, **kwargs)

    def on_disconnect(self):
        for f in Registry.disconnect_list:
            f(self, *args, **kwargs)

    def exposed_setup(self, exp_dict, conf):
        exp_dict = copy.deepcopy(exp_dict)
        conf = copy.deepcopy(conf)
        for f in Registry.setup_list:
            f(self, exp_dict, conf)

    def exposed_launch(self):
        for f in Registry.launch_list:
            f(self, *args, **kwargs)
        pass

    def exposed_run(self):
        for f in Registry.run_list:
            f(self, *args, **kwargs)

    def exposed_teardown(self):
        for f in Registry.teardown_list:
            f(self, *args, **kwargs)
