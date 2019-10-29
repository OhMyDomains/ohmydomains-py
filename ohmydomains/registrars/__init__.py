from importlib import import_module
from ohmydomains.util import ObjectDict


class UnsupportedRegistrarError(Exception): pass


SUPPORTED_REGISTRARS = (
	'namecheap',
	'namesilo',
	'name',
	'dynadot',
	'zeit',
	'gandi',
)
'''Supported registrars.
Each entry corresponds to a submodule in `ohmydomains.registrars`.'''


def get_registrar(name):
	module = import_module('.' + name, 'ohmydomains.registrars')
	for attr in dir(module):
		if attr not in ('Account', 'RegistrarAccount') and attr.endswith('Account'):
			module.Account = getattr(module, attr)
	return module


registrars = ObjectDict({ name: get_registrar(name) for name in SUPPORTED_REGISTRARS })

