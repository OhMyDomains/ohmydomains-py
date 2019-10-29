import json
import requests
import requests.auth
import pendulum
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.domain import Domain
from ohmydomains.contact import ContactList
from ohmydomains.util import RequestFailed


class ZeitAccount(RegistrarAccount):
	'''Registrar API for https://zeit.co:[ZEIT].
	'''

	REGISTRAR = 'zeit'
	REGISTRAR_NAME = 'ZEIT'
	API_BASE = 'https://api.zeit.co'
	NEEDED_CREDENTIALS = ('token',)

	def _request(self, endpoint, method='get', data={}):
		data = getattr(requests, method)(self.API_BASE + endpoint, headers={
			'Authorization': 'Bearer ' + self._credentials['token']
		}, json=data).json()

		if 'error' in data:
			raise RequestFailed(data['error'], method, endpoint, data, self)

		return data
	
	def test_credentials(self):
		try:
			self._try_request('/www/user')
			return True
		except:
			return False

	def iter_domains(self, **criteria):
		for raw_domain in self._try_request('get', 'v4/domains')['domains']:
			# https://zeit.co/docs/api/#endpoints/domains
			# '... null if not bought with ZEIT.'
			if raw_domain['expiresAt'] == 'null':
				continue

			yield Domain(
				contacts=ContactList(),
				account=self,

				name=raw_domain['name'],
				registrar_name=self.REGISTRAR_NAME,
				creation=pendulum.from_timestamp(raw_domain['createdAt'] / 1000),
				expiry=pendulum.from_timestamp(raw_domain['expiresAt'] / 1000),
				name_servers=raw_domain['nameservers'],
				# ZEIT will not even ask for your contact info on registration.
				whois_privacy=True
			)

