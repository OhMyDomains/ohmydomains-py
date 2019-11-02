from ohmydomains.registrars.account import RegistrarAccount


class DynadotAccount(RegistrarAccount):
	API_BASE = 'https://api.dynadot.com/api3.xml'
	NEEDED_CREDENTIALS = ('api_key',)

