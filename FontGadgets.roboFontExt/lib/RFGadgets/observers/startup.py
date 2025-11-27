import os
import sys
import importlib
import inspect
from mojo.subscriber import Subscriber
from mojo.extensions import getExtensionDefault

EXTENSION_ID = "design.bahman.fontgadgets"
SUBSCRIBERS_KEY = f"{EXTENSION_ID}.subscribers"

def getRoboFontGadgetsSubscribers():
    subscribers = []
    basePath = os.path.dirname(__file__)
    subscribersPath = os.path.join(basePath, "subscribers")
    if subscribersPath not in sys.path:
        sys.path.append(subscribersPath)
    if not os.path.exists(subscribersPath):
        raise ModuleNotFoundError(subscribersPath)
    for f in os.listdir(subscribersPath):
        if f.endswith(".py") and (not f.startswith("_")):
            moduleName = f[:-3]
            if moduleName == 'base':
                continue
            try:
                module = importlib.import_module(moduleName)
                for name, obj in inspect.getmembers(module):
                    if (
                        inspect.isclass(obj)
                        and issubclass(obj, Subscriber)
                        and (obj is not Subscriber)
                    ):
                        if obj.__module__ == module.__name__:
                            subscribers.append(obj)
            except Exception as e:
                print(f"Error loading module {moduleName}: {e}")
    return subscribers


def startActivatedObservers():
    subs = getRoboFontGadgetsSubscribers()
    extensionSettings = getExtensionDefault(SUBSCRIBERS_KEY, {})
    log = ['List of FontGadgets subscribers:']
    for sub in subs:
        subName = sub.__name__
        message = f"\t'{subName}': "
        toActive = extensionSettings.get(sub.__name__, False)
        if toActive:
            sub.activate()
            if sub.isActive():
                message += "subscriber is activated."
            else:
                message += "subscriber didn't get activated."
        else:
            message += "subscriber is disabled."
        log.append(message + "\n")
    return log

if __name__ == '__main__':
    startActivatedObservers()
