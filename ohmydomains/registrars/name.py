import requests
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.util import RequestFailed


class NameAccount(RegistrarAccount):
	API_BASE = 'https://api.name.com/v4'
	NEEDED_CREDENTIALS = ('username', 'token')

	CONTACT_KIND_MAP = {
		'registrant': 'registrant',
		'administrative': 'admin',
		'technical': 'tech',
		'billing': 'billing'
	}

	CONTACT_ATTR_MAP = {
		'first_name': 'firstName',
		'last_name': 'lastName',
		'organization': 'companyName',
		'address': 'address1',
		'address_2': 'address2',
		'city': 'city',
		'province': 'state',
		'postal_code': 'zip',
		'country': 'country',
		'phone': 'phone',
		'fax': 'fax',
		'email': 'email'
	}

	def test_credentials(self):
		try:
			self._try_request('/hello')
			return True
		except:
			return False

	def _request(self, endpoint, method='get', params={}, data={}):
		response = getattr(requests, method)(self.API_BASE + endpoint, params=params, json=data)
		json = response.json()
		if response.code != 200:
			raise RequestFailed(json, method, endpoint, params, data, self)
		return json


	def _get_domain(self, name):
		response = self._try_request('/domains/' + name)

		return Domain(
			contacts=ContactList({
				kind: Contact({
					attr: raw_contact[attr_key] for attr, attr_key in self.CONTACT_ATTR_MAP.items()
				}) for kind, kind_key in self.CONTACT_KIND_MAP.items()
			}),
			account=self,

			name=name,
			creation=response['createDate'],
			expiry=response['expireDate'],
			registrar_name=self.REGISTRAR_NAME,

			lock=response['locked'],
			auto_renew=response['autorenewEnabled'],
			whois_privacy=response['privacyEnabled'],
			name_servers=response['nameservers'])
	
	def update_contacts(self, names, contacts):
		finished = []
		data = {
			kind_key: {
				attr_key: contacts[kind][attr] for attr, attr_key in self.CONTACT_ATTR_MAP.items()
			} for kind, kind_key in self.CONTACT_KIND_MAP.items()
		}
		for name in names:
			try:
				self._try_request('/domains/{}:setContacts'.format(name), method='post', data=data)
				finished.append(name)
			except:
				pass
		return finished
	
	def update_name_servers(self, names, servers):
		finished = []
		for name in names:
			try:
				self._try_request('/domains/{}:setNameservers', method='post', data={
					'nameservers': servers
				})
				finished.append(name)
			except:
				pass
		return finished

	def iter_domains(self, **criteria):
		page_id = 1
		total_pages = 2

		while page_id < total_pages:
			response = self._try_request('/domains', params={ 'page': page_id, 'perPage': 1000 })
			total_pages = response['lastPage']
			page_id += 1

			for raw in response['domains']:
				yield self._get_domain(raw['domainName'])
