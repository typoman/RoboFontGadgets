import time
import sys
import importlib
from types import ModuleType
import logging

logger = logging.getLogger(__name__)
# logging.basicConfig(level=logging.DEBUG)

def deepReload(m: ModuleType):
    name = m.__name__  # get the name that is used in sys.modules
    name_ext = name + '.'  # support finding sub modules or packages

    def compare(loaded: str):
        return (loaded == name) or loaded.startswith(name_ext)

    all_mods = tuple(sys.modules)  # prevent changing iterable while iterating over it
    sub_mods = filter(compare, all_mods)

    for pkg in sub_mods:
        p = importlib.import_module(pkg)
        importlib.reload(p)

def timeit(method):
    """
    A decorator that makes it possible to time functions.
    """
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()
        if 'log_time' in kw:
            name = kw.get('log_name', method.__name__.upper())
            kw['log_time'][name] = int((te - ts) * 1000)
        else:
            logger.debug('%r  %2.2f ms' %(method.__name__, (te - ts) * 1000))
        return result
    return timed

def getEnvironment():
    try:
        from mojo.roboFont import CurrentFont
        return "RoboFont"
    except IndexError:
        return "InShell"
