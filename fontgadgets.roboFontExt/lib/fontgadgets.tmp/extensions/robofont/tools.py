import time
import importlib
from types import ModuleType
import AppKit
from warnings import warn
import logging
import sys

logger = logging.getLogger('fontgadgets.timer')
handler = logging.StreamHandler(sys.stdout)
logger.addHandler(handler)

def reloadSubModules(moduleName, skipSubModules=set(), skipPaths=set()):
	"""
	Use this inside RF to reload your packages when you're editing their code.
	"""
	try:
		module = importlib.import_module(moduleName)
	except ModuleNotFoundError:
		return skipSubModules, skipPaths

	assert isinstance(moduleName, str), "The 'moduleName' argument should be a string type!"
	for attributeName in dir(module):
		if attributeName in skipSubModules:
			continue
		fullAttrName = f"{module.__name__}.{attributeName}"
		attribute = getattr(module, attributeName)
		if isinstance(attribute, ModuleType):
			if not hasattr(attribute, '__file__') or attribute.__file__ in skipPaths:
				continue
			skipPaths.add(attribute.__file__)
			skipSubModules.add(fullAttrName)
			skipSubModules, skipPaths = reloadSubModules(fullAttrName, skipSubModules, skipPaths)
	importlib.reload(module)
	return skipSubModules, skipPaths

def timeit(method):
	"""
	A decorator that makes it possible to time functions.
	"""
	def timed(*args, **kw):
		logger.setLevel(logging.DEBUG)
		ts = time.time()
		result = method(*args, **kw)
		te = time.time()
		if 'log_time' in kw:
			name = kw.get('log_name', method.__name__.upper())
			kw['log_time'][name] = int((te - ts) * 1000)
		else:
			logger.debug('%r  %2.2f ms' %(method.__name__, (te - ts) * 1000))
		logger.setLevel(logging.WARNING)
		return result
	return timed

def setRFAtrribute(attrName, value, override=True):
	"""
	Set an attribute that only exist while robofont is open. Use an elaborate name
	to avoid conflicts with other modules.
	"""
	rf = AppKit.NSApp()
	if not hasattr(rf, attrName) or override:
		setattr(rf, attrName, value)
		return
	warn(f"'{attrName}' already exist, use another name or pass 'True' to 'override' in setRFAtrribute function.")

def getRFAtrribute(attrName):
	"""
	Set an attribute that only exist while robofont is open. Use an elaborate name
	to avoid conflicts with other modules.
	"""
	rf = AppKit.NSApp()
	if hasattr(rf, attrName):
		return getattr(rf, attrName)
	warn(f"'{attrName}' doesn't exist!")
