from pathlib import Path
from requests.exceptions import Timeout as RequestTimeout
from appdirs import user_config_dir


CONFIG_BASE_PATH = Path(user_config_dir('ohmydomains-cli'))
CONFIG_PATH = CONFIG_BASE_PATH.joinpath('config.toml')
CACHE_PATH = CONFIG_BASE_PATH.joinpath('cache.toml')


class RequestFailed(Exception): pass
class MaxTriesReached(Exception): pass


class ObjectDict(dict):
	def __init__(self, *args, **kwargs):
		if len(args) == 1 and len(kwargs) == 0 and isinstance(args[0], dict):
			initial = args[0]
		else:
			initial = kwargs
		self.update(initial)
		self.__dict__.update(initial)

	def __getattr__(self, key):
		return self[key]

	def __setattr__(self, key, value):
		self.__dict__[key] = self[key] = value

	def __delattr__(self, key):
		del self.__dict__[key]
		del self[key]

	def __repr__(self):
		return '{}({})'.format(self.__class__.__name__,
			', '.join('{}={}'.format(repr(k), repr(v)) for k, v in self.__dict__.items()))

	def __str__(self):
		return self.__repr__()

