import pendulum
from ohmydomains.registrars import registrars, UnsupportedRegistrarError
from ohmydomains.registrars.account import RegistrarAccount


class Manager:
	'''This class can hold multiple accounts and raw domains,
	and provide aggregate methods on all or some of them and
	their domain names.
	'''

	def __init__(self, accounts=[], raw_domains=[]):
		self.accounts, self.raw_domains = accounts, raw_domains

	def get_accounts(self, registrars=[], criteria=[]):
		'''Get all or search accounts.

		* `registrars`: optional, names defined in `ohmydomains.registrars.SUPPORTED_REGISTRARS`.
		* `criteria`: optional, keywords to search through account credentials.
		'''

		if not registrars and not criteria:
			return self.accounts

		if registrars:
			accounts = [account for account in self.accounts if account.REGISTRAR in registrars]
		else:
			accounts = self.accounts.copy()

		if criteria:
			filtered = []
			for account in accounts:
				meets_criteria = True
				credentials_joint = ','.join(account._credentials.values())
				for criterion in criteria:
					if criterion not in credentials_joint:
						meets_criteria = False
						break
				if meets_criteria:
					filtered.append(account)
			return filtered

		return accounts

	def iter_domains(self, accounts=None, **criteria):
		'''Iterate through tracked domain names, in specified accounts, if any.

		Arguments are the same as of `get_domains()`, except:

		* No sorting functionality, thus related arguments,
		since we are iterating through them.
		'''

		if not accounts:
			accounts = self.accounts.copy()

		for key in ('expiry_before', 'expiry_after', 'creation_before', 'creation_after'):
			if isinstance(criteria.get(key, None), str):
				criteria[key] = pendulum.parse(criteria[key])

		if 'expiry_in' in criteria:
			criteria['expiry_before'] = pendulum.now().add(days=int(criteria['expiry_in']))

		for account in accounts:
			for domain in account.iter_domains(**criteria):
				if 'expiry_before' in criteria and domain.expiry > criteria['expiry_before']:
					continue
				if 'expiry_after' in criteria and domain.expiry < criteria['expiry_after']:
					continue
				if 'creation_before' in criteria and domain.creation > criteria['creation_before']:
					continue
				if 'creation_after' in criteria and domain.creation < criteria['creation_after']:
					continue

				yield domain

	def get_domains(self, accounts=None, sort_by='expiring_before', order='desc', **criteria):
		'''List or search through tracked domain names,
		in specified accounts, if any.

		As this method performs network requests, it will block for quite
		a while under certain conditions. To solve this, you may use
		`iter_domains()` to progressively iterate through them.

		* `accounts`: accounts to search through. If omitted, search through all;
		can be result of `get_accounts()`.
		* `criteria`: keyword arguments, each being one of below:
		** `search`: keywords to search domain names.
		** `search_columns`: which columns to search provided keywords.
		** `expiry_in` / `expiry_before`: only one of them should be present.
		`expiry_in` is in days.
		** `expiry_after`
		** `creation_before`
		** `creation_after`
		** `sort_by`: one of criteria above, `expiring_before` by default.
		** `order`: `asc`ending or `desc`ending, `desc` by default.

		Criteria listed above which are dates should be `datetime.datetime`-like objects,
		or strings in the form of `YYYY/MM/DD`.
		Internally we use `pendulum` to handle them.
		'''


		return sorted(
			self.iter_domains(accounts=accounts or self.accounts.copy(), **criteria),
			key=lambda r: r[sort_by],
			reverse=order == 'desc')

	def add_accounts(self, *accounts):
		'''Add accounts.

		* `accounts`: Each must be an instance of the *Account* class provided by
			submodules in `ohmydomains.registrars`,
			or a dict containing a `registrar` key and corresponding credentials
			required by that registrar.
		'''

		# allow passing in an iterator.
		if len(accounts) == 1 and not isinstance(accounts[0], dict):
			try:
				_iter = iter(accounts[0])
				accounts = _iter
			except:
				pass

		for account in accounts:
			if isinstance(account, RegistrarAccount):
				self.accounts.append(account)
			else:
				if account['registrar'] not in registrars:
					raise UnsupportedRegistrarError(account['registrar'])
				self.accounts.append(registrars[account['registrar']].Account(account['credentials']))

	def delete_accounts(self, *accounts):
		for account in accounts:
			if account not in self.accounts:
				print(account, 'not in', self.accounts)
				continue
			self.accounts.remove(account)
	
	def add_domains(self, *domains):
		'''Manually add domain name(s) not belonging to any stored account.

		Each must be a string and valid domain name.
		'''

		self.raw_domains.extend(domains)

	def whois(self, *names):
		'''Query whois data for provided domain names.
		'''

		for name in names:
			pass

