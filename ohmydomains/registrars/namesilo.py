import requests
import xmltodict
import pendulum
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.domain import Domain
from ohmydomains.contact import Contact, ContactList


class NameSiloAccount(RegistrarAccount):
	API_BASE = 'https://www.namesilo.com/api/'
	REGISTRAR = 'namesilo'
	REGISTRAR_NAME = 'NameSilo'
	NEEDED_CREDENTIALS = ('api_key',)

	CONTACT_ATTR_MAP = {
		'address_2': 'address2',
		'postal_code': 'zip',
	}

	_contact_cache = {}

	@property
	def identifier(self):
		# there's currently no way to get an identifier, username or email,
		# through the API, so we just use part of the key.
		return self._credentials['api_key'][:6]

	def _request(self, operation, data={}):
		params = {
			'version': 1,
			'type': 'xml',
			'key': self._credentials['api_key'],
		}
		params.update(data)

		response = xmltodict.parse(requests.get(self._api_base + operation, params).text)['namesilo']['reply']
		# https://www.namesilo.com/api-reference
		# code=300 means success
		if response['code'] != '300':
			raise RequestFailed(response['detail'], option, data, self)
		return response
	
	def _get_contact_from_id(self, id):
		if id not in self._contact_cache:
			response = self._try_request('contactList', {
				'contact_id': id
			})['contact']
			for attr, attr_key in self.CONTACT_ATTR_MAP.items():
				response[attr] = response[attr_key]
			self._contact_cache[id] = Contact(**response)
		return self._contact_cache[id]
	
	def _get_domain(self, name):
		response = self._try_request('getDomainInfo', {
			'domain': name
		})

		name_servers = response['nameservers']['nameserver']
		if '#text' in name_servers:
			name_servers = [nameservers]
		name_servers = map(lambda i: i['#text'], name_servers)

		return Domain(
			contacts=ContactList({
				kind: self._get_contact_from_id(response['contact_ids'][kind]) for kind in response['contact_ids']
			}),
			account=self,

			name=name,
			creation=pendulum.parse(response['created']),
			expiry=pendulum.parse(response['expires']),
			registrar_name=self.REGISTRAR_NAME,

			lock=response['locked'] == 'Yes',
			auto_renew=response['auto_renew'] == 'Yes',
			whois_privacy=response['private'] == 'Yes',
			name_servers=name_servers)

	def update_contacts(self, names, contacts):
		pass
	
	def update_name_servers(self, names, name_servers):
		if len(names) > 200:
			raise Exception('Must provide no more than 200 domain names.')
		if 2 < len(name_servers) < 13:
			raise Exception('Must provide at least 2 and at most 13 name servers.')

		params = { 'domain': ','.join(names) }
		for i in range(len(name_servers)):
			params['ns' + str(i + 1)] = name_servers[i]

		self._try_request('changeNameServers', params=params)
		return names

	def iter_domains(self, **criteria):
		response = self._try_request('listDomains')['domains']
		if response:
			names = response['domain']
			# in case there is exactly one result and it's not parsed as list
			if isinstance(names, str):
				names = [names]

			for name in names:
				yield self._get_domain(name)
		else:
			yield

