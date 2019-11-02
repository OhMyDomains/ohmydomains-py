from ohmydomains.util import ObjectDict


class Domain(ObjectDict):
	'''Internal class representing a domain name.
	'''

	FIELDS = (
		# internal implementations
		'account', 'contacts',
		# fields at least they all have
		'name', 'registrar_name',
		'creation', 'expiry',
		'name_servers',
		'status',

		# maybe have, maybe not; there are essentially three states,
		# true, false, unknown.
		# True, False, None.
		# compare them to exact values, not boolean results.
		'lock',
		'auto_renew',
		'whois_privacy'
	)
	'''Available fields of a domain name.'''

	def __init__(self, contacts=None, account=None, **data):
		data = { key: value for key, value in data.items() if key in self.FIELDS }
		super().__init__(data)
		for key in self.FIELDS:
			if key not in self:
				self[key] = None
		self.contacts, self.account = contacts, account

	def update_contacts(self, contacts=None):
		'''Try updating contacts of this domain name to registrar.
		'''

		try:
			if not contacts:
				contacts = self.contacts
			self.account.update_contacts([self.name], contacts)
		except:
			pass

	def update_name_servers(self, name_servers):
		'''Try updating name servers of this domain name to registrar.
		'''

		try:
			self.account.update_name_servers([self.name], name_servers)
		except:
			pass

