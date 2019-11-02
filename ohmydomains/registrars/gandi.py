from math import ceil
import requests
import pendulum
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.domain import Domain
from ohmydomains.contact import Contact, ContactList
from ohmydomains.util import RequestFailed


class GandiAccount(RegistrarAccount):
	REGISTRAR_NAME = 'Gandi'
	API_BASE = 'https://api.gandi.net/v5'
	API_BASE_TESTING = ''
	NEEDED_CREDENTIALS = ('api_key',)
	LIST_PER_PAGE = 100

	CONTACT_KIND_MAP = {
		'registrant': 'owner',
		'administrative': 'admin',
		'technical': 'tech',
		'billing': 'bill'
	}

	CONTACT_ATTR_MAP = {
		'first_name': 'given',
		'last_name': 'family',
		'organization': 'orgname',
		'address': 'streetaddr',
		'city': 'city',
		'province': 'state',
		'country': 'country',
		'postal_code': 'zip',
		'phone': 'phone', # but there is also 'mobile'.
		'email': 'email'
	}

	def __init__(self, **kwargs):
		super().__init__(**kwargs)

		self._auth_header = {
			'Authorization': 'Apikey '.format(self._credentials['api_key'])
		}

	def _request(self, endpoint, method='get', params=None, data=None):
		response = getattr(requests, method)(self._api_base + endpoint, headers=self._auth_header, params=params, json=data)
		json = response.json()
		if response.status_code != 200:
			raise RequestFailed(json, endpoint, method, params, data, self)
		return (json, response.headers)
	
	def test_credentials(self):
		try:
			self._try_request('/domain/check', params={ 'name': 'example.com' })
			return True
		except:
			return False
	
	def _get_contacts(self, name):
		data = self._try_request('/domain/domains/{}/contacts'.format(name))
		return ContactList({
			kind: Contact({
				attr: data[kind_key].get(attr_key, None) for attr, attr_key in self.CONTACT_ATTR_MAP.items()
			}) for kind,  kind_key in self.CONTACT_KIND_MAP.items()
		})
	
	def update_contacts(self, names, contacts):
		pass

	def update_name_servers(self, names, servers):
		finished = []
		for name in names:
			try:
				self._try_request('/domain/domains/{}/nameservers'.format(name), method='put', data={
					'nameservers': servers
				})
				finished.append(name)
			except:
				pass
		return finished
	
	def iter_domains(self, **criteria):
		page_id = 1
		total_pages = 2

		params = {
			'page': page_id,
			'per_page': self.LIST_PER_PAGE
		}
		if criteria.get('search', None):
			params['fqdn'] = criteria['search']

		while page_id < total_pages:
			data, headers = self._try_request('/domain/domains', params=params)
			total_pages = ceil(headers['Total-Count'] / self.LIST_PER_PAGE)
			page_id += 1

			for raw in data:
				yield Domain(
					account=self,
					contacts=self._get_contacts(raw['fqdn']),

					name=raw['fqdn'],
					creation=pendulum.parse(raw['dates'].get('created_at', ['registry_created_at'])),
					expiry=pendulum.parse(raw['dates'].get('deletes_at', raw['dates'].get('registry_ends_at', None))),
					registrar_name=self.REGISTRAR_NAME,

					auto_renew=raw['autorenew'],
					name_servers=[raw['nameserver']['current']] + raw['nameserver'].get('hosts', []))
