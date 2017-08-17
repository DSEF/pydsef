import rpyc
from rpyc.utils.server import ThreadedServer
import copy
import inspect
import shutil
import os

class Registry:
    """Class for registering experiment funcionts."""
    connect_list = []
    disconnect_list = []
    setup_list = []
    launch_list = []
    run_fun = None
    teardown_list = []

    server = None

    @staticmethod
    def connect(fun):
        """Decoration for registering 'connect' functions. These functions are run when
        the Jupyter server connects to the master node over RPyC."""
        Registry.connect_list.append(fun)
        return fun

    @staticmethod
    def disconnect(fun):
        """Decoration for registering 'disconnect' functions. These functions are run when
        the Jupyter server disconnects from the RPyC server running on the master node."""
        Registry.disconnect_list.append(fun)
        return fun

    @staticmethod
    def setup(fun):
        """Decoration for registering 'setup' functions. These functions are run during the
        setup phase of each trial in an experiment."""
        Registry.setup_list.append(fun)
        return fun

    @staticmethod
    def launch(fun):
        """Decoration for registering 'launch' functions. These functions are run during the
        launch phase of each trial in an experiment."""
        Registry.launch_list.append(fun)
        return fun

    @staticmethod
    def run(fun):
        """Deocration for registering a 'run' function. You can only register one of these. This
        function is executed during the run phase of each trial in an experiment."""
        if Registry.run_fun == None:
            Registry.run_fun = fun
        else:
            raise Exception
        return fun

    @staticmethod
    def teardown(fun):
        """Decoration for registering 'teardown' functions. These functions are run during the
        teardown phase of each trial in an experiment."""
        Registry.teardown_list.append(fun)
        return fun

    @staticmethod
    def experiment(cls, port = 18861):
        """Class decoration for registering an experiment service. This automatically adds an archive
        function to the class as well as starting a ThreadedServer RPyC instance."""
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
    """Base class for the experimental run object. None of these methods are meant to be called by a user.
    They are called at the appropiate time during an experiment."""

    def on_connect(self, *args, **kwargs):
        """Needed by rpyc.Service superclass. This calls all registered 'connect' functions at the appropiate time."""
        for f in Registry.connect_list:
            f(self, *args, **kwargs)

    def on_disconnect(self, *args, **kwargs):
        """Needed by rpyc.Service superclass. This calls all registered 'disconnect' functions at the appropiate time."""
        for f in Registry.disconnect_list:
            f(self, *args, **kwargs)

    def exposed_setup(self, exp_dict, conf):
        """This exposes a 'setup' function on the RPyC service.
        During an experiment this is connected to from Jupyter and executed on the master node.
        All registered 'setup' functions will be called when this function is called.
        This function additionally defines member variables using the passed in  exp_dict."""
        exp_dict = copy.deepcopy(exp_dict)
        conf = copy.deepcopy(conf)
        for key in exp_dict:
            setattr(self, key, exp_dict[key])
        for f in Registry.setup_list:
            f(self, exp_dict, conf)

    def exposed_launch(self, *args, **kwargs):
        """This exposes a 'launch' function on the RPyC service.
        During an experiment this is connected to from Jupyter and executed on the master node.
        All registered 'launch' functions will be called when this function is called."""
        for f in Registry.launch_list:
            f(self, *args, **kwargs)

    def exposed_run(self, *args, **kwargs):
        """This exposes a 'run' function on the RPyC service.
        During an experiment this is connected to from Jupyter and executed on the master node.
        The registered 'run' function will be called when this function is called."""
        return Registry.run_fun(self, *args, **kwargs)

    def exposed_teardown(self, *args, **kwargs):
        """This exposes a 'teardown' function on the RPyC service.
        During an experiment this is connected to from Jupyter and executed on the master node.
        All registered 'teardown' functions will be called when this function is called."""
        for f in Registry.teardown_list:
            f(self, *args, **kwargs)
