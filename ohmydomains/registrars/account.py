from ohmydomains.util import RequestTimeout, MaxTriesReached


class RegistrarAccount:
	REGISTRAR = 'registrar'
	REGISTRAR_NAME = 'Registrar'
	
	NEEDED_CREDENTIALS = ()
	OPTIONAL_CREDENTIALS = ()

	def __init__(self, net_init=True, **credentials):
		self._credentials = credentials

	def export(self):
		return {
			'registrar': self.REGISTRAR,
			'credentials': self._credentials
		}
	
	def test_credentials(self): return True
	
	def _request(self, *args, **kwargs): pass

	def _try_request(self, *args, max_tries=3, **kwargs):
		tries = 0
		response = None
		while tries < max_tries:
			try:
				response = self._request(*args, **kwargs)
				break
			except RequestTimeout:
				tries += 1

		if tries == max_tries and not response:
			raise MaxTriesReached(self, tries)

		return response
	
	def update_contacts(self, names, contacts): pass

	def update_name_servers(self, names, servers): pass
	
	def iter_domains(self, **criteria): pass

	def get_domains(self, *args, **kwargs):
		return [i for i in self.iter_domains(*args, **kwargs)]

