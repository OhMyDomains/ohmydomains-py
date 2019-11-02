from ohmydomains.util import RequestTimeout, MaxTriesReached


class RegistrarAccount:
	REGISTRAR = 'registrar'
	REGISTRAR_NAME = 'Registrar'
	API_BASE = ''
	API_BASE_TESTING = ''
	
	NEEDED_CREDENTIALS = ()
	OPTIONAL_CREDENTIALS = ()

	def __init__(self, testing=False, net_init=True, tags=[], **credentials):
		self._credentials = credentials
		self.is_testing_account = testing
		self.tags = tags
		self._api_base = testing and self.API_BASE_TESTING or self.API_BASE

	def export(self):
		return {
			'registrar': self.REGISTRAR,
			'credentials': self._credentials,
			'testing': self.is_testing_account,
			'tags': self.tags
		}
	
	@property
	def identifier(self): pass

	@property
	def unique_identifier(self):
		return '{}:{}'.format(self.REGISTRAR_NAME, self.identifier)
	
	def test_credentials(self): return True
	
	def _request(self, *args, **kwargs): pass

	def _try_request(self, *args, max_tries=3, **kwargs):
		tries = 0
		response = None
		while tries < max_tries:
			try:
				response = self._request(*args, **kwargs)
				break
			except:
				tries += 1
		if tries == max_tries and not response:
			raise MaxTriesReached(self, tries)

		return response
	
	def update_contacts(self, names, contacts): pass

	def update_name_servers(self, names, servers): pass
	
	def iter_domains(self, **criteria): pass

	def get_domains(self, *args, **kwargs):
		return [i for i in self.iter_domains(*args, **kwargs)]

