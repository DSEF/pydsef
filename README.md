# PyDSEF
A python module that provides the python interface of dsef. Here is a template of how to use this: [python-dsef](https://github.com/DSEF/dsef-python)

## Installing
You can install with: `pip3 install pydsef`, or if you are developing `python3 setup.py install`

## Files
### `experiment.py` 
Contains the experiment class which is the entry point to all experiments in dsef.
This manages settings, experiment generation, setting up RPyC servers, transfering files, and running experiments.
This is meant to be used from within Jupyter.

### `service.py`
Contains a rpyc.Service subclass and a set of decorators to be used when defining your experiment service.

### `util.py`
Provides a series of utility functions that are used throughout DSEF
