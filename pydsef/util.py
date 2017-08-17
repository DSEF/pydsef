from collections import Iterable
import yaml
import threading
from time import sleep
from queue import Queue

class Included:
    """Custom list object for use in DSEFLoader."""
    def __init__(self, l):
        self.lst = l

    def __str__(self):
        return "[{}]".format('; '.join([str(i) for i in self.lst]))

    def __repr__(self):
        return self.__str__()

class DSEFLoader(yaml.Loader):
    """Custom YAML Loader with the !include tag to mark changing parameters in experiments."""
    @staticmethod
    def init():
        DSEFLoader.add_constructor("!include", DSEFLoader.include)

    @staticmethod
    def include(loader, node):
        return Included(loader.construct_sequence(node))

def product(d):
    """Returns a list of dictionaries that represent the product of all the values marked with !include."""
    result = [{}]

    def add_dict(d1, d2):
        d1 = d1.copy()
        d1.update(d2)
        return d1

    for key, value in d.items():
        if isinstance(value, Included):
            result = [add_dict(x,{key:y}) for x in result for y in value.lst]
        else:
            result = [add_dict(x,{key:value}) for x in result]

    return result

def show_progress(fun, msg, args = (), rate = 0.3):
    """Displays a spinner while the given function is running."""
    q = Queue()
    def new_fun(q, a):
        q.put(fun(*a))
    t = threading.Thread(target = new_fun, args = (q, args))
    t.start()

    loading = ['|', '/', '-', '\\']
    i = 0
    while t.isAlive():
        print('[{}] {}'.format(loading[i % len(loading)], msg), end='\r')
        i += 1
        sleep(rate)
    t.join()
    print("\r[+]")
    return q.get()
