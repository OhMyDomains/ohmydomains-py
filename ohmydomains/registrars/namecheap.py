import requests
import xmltodict
import pendulum
from math import ceil
from ohmydomains.domain import Domain
from ohmydomains.contact import Contact, ContactList
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.util import RequestFailed


def get_ip_address():
	# Thank you fellas
	return requests.get('https://api.ipify.org/?format=raw').text


def get_date(date_str):
	# Hello, American
	return pendulum.from_format(date_str, 'MM/DD/YYYY')

class NameCheapAccount(RegistrarAccount):
	'''Registrar API for https://www.namecheap.com:[NameCheap].

	Get your API key at https://ap.www.namecheap.com/settings/tools/apiaccess/

	* `credentials`
	** `api_user`
	** `api_key`
	** `username`: optional
	** `client_ip`: optional, will retrieve from online API if omitted

	Read about details at https://www.namecheap.com/support/api/global-parameters/
	'''

	REGISTRAR = 'namecheap'
	REGISTRAR_NAME = 'NameCheap'
	API_BASE = 'https://api.namecheap.com/xml.response'
	API_BASE_TESTING = 'https://api.sandbox.namecheap.com/xml.response'
	NEEDED_CREDENTIALS = ('api_user', 'api_key')
	OPTIONAL_CREDENTIALS = ('username', 'client_ip')

	CONTACT_TYPE_MAP = {
		'registrant': 'Registrant',
		'technical': 'Tech',
		'administrative': 'Admin',
		'billing': 'AuxBilling'
	}

	CONTACT_ATTR_MAP = {
		'first_name': 'FirstName',
		'last_name': 'LastName',
		'organization': 'OrganizationName',
		'title': 'JobTitle',
		'address': 'Address1',
		'address_2': 'Address2',
		'city': 'City',
		'province': 'StateProvince',
		'postal_code': 'PostalCode',
		'country': 'Country',
		'phone': 'Phone',
		'phone_ext': 'PhoneExt',
		'fax': 'Fax',
		'email': 'EmailAddress'
	}


	def __init__(self, client_ip=None, net_init=True, **credentials):
		super().__init__(**credentials)
		# NameCheap requires your IP address to be whitelisted.
		# Understandable for security's sake.
		# But send it through URL params? Why? Can't you get it yourself?
		# And only IPv4 can be used.
		# Good job NameCheap.
		if client_ip:
			self._client_ip = self._credentials['client_ip'] = client_ip
		elif net_init:
			self._fill_ip_address()
		else:
			self._client_ip = '2.3.3.3'

		self._global_params = {
			'ApiUser': self._credentials['api_user'],
			'ApiKey': self._credentials['api_key'],
			'UserName': self._credentials.get('username', self._credentials['api_user']),
			'ClientIp': self._client_ip
		}

	@property
	def identifier(self):
		return self._global_params['UserName']
	
	def _fill_ip_address(self):
		self._client_ip = get_ip_address()
	
	def _request(self, command, data={}):
		# https://www.namecheap.com/support/api/global-parameters/
		params = { 'Command': command }
		params.update(self._global_params)
		params.update(data)

		response = requests.get(self._api_base, params=params)
		data = xmltodict.parse(response.text)['ApiResponse']
		if data['@Status'] != 'OK':
			errors = data['Errors']['Error']
			if '#text' in errors:
				errors = [errors]
			raise RequestFailed(map(lambda i: i['#text'], errors), command, data, self)
		return data['CommandResponse']
	
	def test_credentials(self):
		try:
			self._try_request('namecheap.domains.check', { 'DomainList': 'example.com' })
			return True
		except:
			return False

	def _get_contacts(self, name):
		data = self._try_request('namecheap.domains.getContacts', {
			'DomainName': name
		})['DomainContactsResult']

		contacts = ContactList()
		for kind, kind_key in self.CONTACT_TYPE_MAP.items():
			contacts[kind] = Contact(kind, {
				attr: data[kind_key][attr_key] for attr, attr_key in self.CONTACT_ATTR_MAP.items()
			})

		return contacts

	def _get_name_servers(self, name):
		dot_pos = name.index('.')
		return self._try_request('namecheap.domains.dns.getList', {
			# WTF NameCheap?
			'SLD': name[:dot_pos],
			'TLD': name[dot_pos + 1:]
			})['DomainDNSGetListResult']['Nameserver']

	def update_name_servers(self, names, name_servers):
		'''Update name servers for given domain names.

		Returns domain names finished updating.
		'''

		dot_pos = name.index('.')

		finished = []

		for name in names:
			try:
				self._try_request('namecheap.domains.dns.setCustom', {
					'SLD': name[:dot_pos],
					'TLD': name[dot_pos + 1:],
					'Nameservers': ','.join(name_servers)
				})
				finished.append(name)
			except:
				pass

		return finished

	def update_contacts(self, names, contacts):
		'''Update contacts for given domain names.

		* `names`: `str[]` list of domain names to update
		* `contacts`: `dict`-like object holding one or more kinds of
			contact info

		Returns domain names finished updating.
		'''

		finished = []

		for name in names:
			params = { 'DomainName': name }
			for kind, kind_key in self.CONTACT_TYPE_MAP.items():
				for attr, attr_key in self.CONTACT_KEY_MAP.items():
					params[kind_key + attr_key] = contacts[kind][attr]

			try:
				self._try_request('namecheap.domains.setContacts', params)
				finished.append(name)
			except:
				pass

		return finished

	def iter_domains(self, search=None, **criteria):

		page_id = 1
		total_pages = 2

		params = {
			# https://www.namecheap.com/support/api/methods/domains/get-list/
			# Maximum is 100, so we use that to reduce request count.
			'PageSize': 100
		}

		if search:
			params['SearchTerm'] = search

		while page_id < total_pages:
			params['Page'] = page_id
			data = self._try_request('namecheap.domains.getList', params)
			total_pages = ceil(int(data['Paging']['TotalItems']) / int(data['Paging']['PageSize']))
			page_id += 1
			raw_domains = data['DomainGetListResult']['Domain']
			# in case there is exactly one result and it's not parsed as list
			if '@Name' in raw_domains:
				raw_domains = [raw_domains]

			for raw_domain in data['DomainGetListResult']['Domain']:
				yield Domain(
					contacts=self._get_contacts(raw_domain['@Name']),
					account=self,

					name=raw_domain['@Name'],
					creation=get_date(raw_domain['@Created']),
					expiry=get_date(raw_domain['@Expires']),
					registrar_name=self.REGISTRAR_NAME,

					lock=raw_domain['@IsLocked'] == 'true',
					auto_renew=raw_domain['@AutoRenew'] == 'true',
					whois_privacy=raw_domain['@WhoisGuard'] == 'ENABLED',
					name_servers=self._get_name_servers(raw_domain['@Name']))

