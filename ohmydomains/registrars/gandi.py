import xmlrpc.client
import functools
from ohmydomains.registrars.account import RegistrarAccount


class GandiAccount(RegistrarAccount):
	REGISTRAR_NAME = 'Gandi'
	RPC_ENDPOINT = 'https://rpc.gandi.net/xmlrpc/'
	NEEDED_CREDENTIALS = ('api_key',)


	def __init__(self, **credentials):
		super().__init__(**credentials)
		self._client = xmlrpc.client.ServerProxy(self.RPC_ENDPOINT)

