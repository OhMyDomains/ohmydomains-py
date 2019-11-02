def name(domain): return domain.name
def registrar_name(domain): return domain.registrar_name
def creation(domain): return domain.creation.to_date_string()
def expiry(domain): return domain.expiry.to_date_string()
def name_servers(domain): return '\n'.join(domain.name_servers)
def status(domain): return domain.status


TRINARY_STATE = {
	True: 'enabled',
	False: 'disabled',
	None: 'unknown'
}
def lock(domain): return TRINARY_STATE[domain.lock]
def auto_renew(domain): return TRINARY_STATE[domain.auto_renew]
def whois_privacy(domain): return TRINARY_STATE[domain.whois_privacy]


def account(domain): return domain.account.unique_identifier + (domain.account.is_testing_account and '(testing)' or '')


def contacts(domain):
	return '\n'.join(domain.contacts.registrant[field] for field in domain.contacts.registrant.FIELDS)
