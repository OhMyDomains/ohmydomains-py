from ohmydomains.util import ObjectDict


class Contact(ObjectDict):
	'''Internal class holding contact information for a specific kind.
	'''

	FIELDS = (
		'kind',
		'first_name', 'last_name',
		'address', 'address_2', 'city', 'province', 'country', 'postal_code',
		'phone', 'phone_ext', 'email',
	)

	def __init__(self, **data):
		data = { key: value for key, value in data.items() if key in self.FIELDS }
		super().__init__(data)
		for key in self.FIELDS:
			if key not in self:
				self[key] = None


class ContactList(ObjectDict):
	'''Internal class holding four kinds of domain contacts.'''

	KINDS = ('registrant', 'technical', 'administrative', 'billing')

	def __init__(self, *args, **contacts):
		if len(args) > 0 and isinstance(args[0], dict):
			contacts = args[0]

		for kind in self.KINDS:
			self.__dict__[kind] = contacts.get(kind, None) or Contact(kind=kind)

	def __getattr__(self, key):
		if key in self.KINDS:
			return self[key]

