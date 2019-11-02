import pendulum
from whois import whois
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.domain import Domain
from ohmydomains.contact import Contact, ContactList


class RawDomains(RegistrarAccount):
	def __init__(self, domains=[]):
		self._domains = domains

	def export(self):
		return { 'credentials': { 'domains': self._domains } }

	def add_domains(self, *names):
		self._domains.extend(names)

	def iter_domains(self, **criteria):
		for name in self._domains:
			raw = whois(name)

			# The `python-whois` package is a great effort to parsing largely varying formats of whois data,
			# and due to its community contributed nature, has yet to have a "standard" way of format.
			# We should consider helping on that.

			yield Domain(
				# contacts=ContactList(),
				account=self,

				name=name,
				registrar_name=raw.get('registrar', None),
				creation=pendulum.from_timestamp(raw['creation_date'].timestamp()),
				expiry=pendulum.from_timestamp(raw['expiration_date'].timestamp()),
				name_servers=raw.get('name_servers', []),
				status=raw.get('status', None)
			)

