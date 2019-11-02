from importlib import import_module
from ohmydomains.registrars import SUPPORTED_REGISTRARS


registrar_cli_modifiers = {}
for name in SUPPORTED_REGISTRARS:
	try:
		registrar_cli_modifiers[name] = import_module('.' + name, 'cli.registrars')
	except: pass

