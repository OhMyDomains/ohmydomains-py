import os.path
import toml
import click
from tabulate import tabulate
import appdirs
from ohmydomains.util import CONFIG_BASE_PATH, CONFIG_PATH, CACHE_PATH
from ohmydomains.manager import Manager
from ohmydomains.domain import Domain
from ohmydomains.registrars.account import RegistrarAccount
from ohmydomains.registrars import registrars
from .registrars import registrar_cli_modifiers

# monkey patch RegistrarAccount._try_request to exit on network failure.
def _exit_on_failure_try_request(self, *args, **kwargs):
	try:
		return self._do_try_request(*args, **kwargs)
	except:
		click.echo('')
		click.echo('Network requests unsuccessful. Please try again later.')
		import sys
		sys.exit()
RegistrarAccount._do_try_request = RegistrarAccount._try_request
RegistrarAccount._try_request = _exit_on_failure_try_request


def load_config():
	if not CONFIG_BASE_PATH.exists():
		CONFIG_BASE_PATH.mkdir()

	return toml.loads(CONFIG_PATH.read_text())


def save_config(data):
	CONFIG_PATH.write_text(toml.dumps(data))


def load_cache():
	return toml.loads(CACHE_PATH.read_text())


def save_cache(data):
	CACHE_PATH.write_text(toml.dumps(data))


def load_manager(manager, net_init=True):
	data = load_config()
	manager.add_accounts((registrars[record['registrar']].Account(
		net_init=net_init,
		testing=record['testing'],
		tags=record['tags'],
		**record['credentials']) for record in data.get('accounts', [])))
	manager.add_domains(*data.get('raw_domains'))


def save_manager(manager):
	data = load_config()
	data['accounts'] = [account.export() for account in manager.accounts]
	data['raw_domains'] = manager.raw_domains
	save_config(data)


manager = Manager()


@click.group()
def cli():
	'''Oh My Domains is an API and CLI
	to manage your domain names in one place.
	'''
	pass


@cli.group()
def domains(): pass


DEFAULT_COLUMNS = ('name', 'account', 'creation', 'expiry', 'auto_renew')
@cli.command('list')
@click.option('-w', '--columns',
	help='''Comma separated list of columns to show.
	Available: {}.
	Default is "{}"'''.format(', '.join(Domain.FIELDS), ','.join(DEFAULT_COLUMNS)))
@click.option('-r', '--registrars', help='Comma separated list of registrars.')
@click.option('-a', '--accounts', help='Comma separated list of (part of) account identifiers.')
@click.option('-t', '--account-tags', help='Comma separated list of (part of) account tags.')
@click.option('-d', '--expiring-in-30-days', is_flag=True,
	help='List only domain name expiring in 30 days. Equals to -D 30.')
@click.option('-D', '--expiry-in', help='List only domain names expiring in this many days.')
@click.option('-e', '--expiry-before', help='List only domain names expiring after this date.')
@click.option('-E', '--expiry-after', help='List only domain names expiring after this date.')
@click.option('-c', '--creation-before', help='List only domain names created before this date.')
@click.option('-C', '--creation-after', help='List only domain names created after this date.')
@click.option('-s', '--sort-by', default='expiry',
	help='Sort result by specified column. Default is by expiry.')
@click.option('-o', '--order', type=click.Choice(['desc', 'asc']), default='asc',
	help='Order of result. Default is ascending (thus earliest expiry first).')
@click.argument('criteria', nargs=-1)
def list_domains(columns, registrars, accounts, account_tags, expiring_in_30_days, 
	sort_by, order,
	**criteria):
	'''List or search domain names in tracked accounts and manually tracked ones.

	All date values are in the form of YYYY-MM-DD.
	'''

	from . import list_domains_output as output

	registrars = registrars and registrars.split(',') or []
	account_criteria = accounts and accounts.split(',') or []
	account_tags = account_tags and account_tags.split(',') or []
	load_manager(manager)
	accounts = manager.get_accounts(registrars=registrars, criteria=account_criteria, tags=account_tags)

	if columns:
		columns = columns.split(',')
	else:
		columns = DEFAULT_COLUMNS
	if 'name' not in columns:
		columns = ['name'] + columns
	
	if expiring_in_30_days:
		criteria['expiry_in'] = 30

	domains = []
	click.echo('Retrieving data for domain # ', nl=False)
	for domain in manager.iter_domains(accounts=accounts, **criteria):
		click.echo('\b' * len(str(len(domains))), nl=False)
		domains.append(domain)
		click.echo(len(domains), nl=False)
	click.echo('\nDone. {} domain name{} in total.'.format(len(domains), len(domains) > 1 and 's' or ''))
	domains = sorted(domains, key=lambda domain: domain[sort_by], reverse=order == 'desc')
	click.echo(tabulate([[getattr(output, k)(domain) for k in columns] for domain in domains], headers=columns))


@cli.group()
def accounts(): pass


LIST_ACCOUNTS_HEADER = ('registrar', 'identifier', 'tags')
@accounts.command('list', help='List or search accounts.')
@click.option('-r', '--registrars', help='Comma separated list of registrars.')
@click.option('-t', '--tags', help='Comma separated list of tags.')
@click.argument('criteria', nargs=-1)
def list_accounts(registrars, tags, criteria):
	load_manager(manager, net_init=False)
	accounts = manager.get_accounts(registrars=registrars, tags=tags, criteria=criteria)
	table = ((account.REGISTRAR_NAME, (account.identifier + (account.is_testing_account and '(testing)' or '')), ','.join(account.tags)) for account in accounts)
	click.echo(tabulate(table, headers=LIST_ACCOUNTS_HEADER))


@accounts.command('track', help='''Track a registrar account.
Enter credentials in the form of pairs of KEY:VALUE, which vary by registrar.
''')
@click.argument('registrar', required=True)
@click.argument('credentials', nargs=-1)
@click.option('-t', '--tags', help='Comma separated list of tags. Tag it to more easily recognize later.')
def track_account(registrar, credentials, tags):
	if registrar not in registrars:
		return click.echo('Registrar {} is not supported yet. Sorry.'.format(registrar))
	
	account = None

	if registrar in registrar_cli_modifiers:
		registrar_track_account = getattr(registrar_cli_modifiers[registrar], 'track_account', None)
		if registrar_track_account:
			try:
				account = registrar_track_account(credentials)
			except:
				return click.echo('Failed tracking account. Please check and try again.')
				
	if not account:
		registrar = registrars[registrar]
		
		if credentials:	
			try:
				credentials = { pair[0]: pair[1] for pair in (kv.split(':') for kv in credentials) }
			except:
				return click.echo('Invalid input. Please enter as prompted.')
		else:
			click.echo('Please enter your credentials below.')
			credentials = {}
			for key in registrar.Account.NEEDED_CREDENTIALS:
				value = None
				while not value:
					value = click.prompt(key)
				credentials[key] = value

		try:
			account = registrar.Account(**credentials)
			click.echo('Testing credentials...')
			if not account.test_credentials(): raise Exception
		except:
			return click.echo('Failed tracking account. Please check and try again.')

	if tags:
		account.tags = tags.split(',')
	
	load_manager(manager, net_init=False)
	manager.add_accounts(account)
	save_manager(manager)
	click.echo('Account tracked.')


@accounts.command('untrack')
@click.argument('criteria', nargs=-1, required=True)
def untrack_accounts(criteria):
	load_manager(manager, net_init=False)
	to_be_untracked = manager.get_accounts(criteria=criteria)
	if not to_be_untracked:
		return click.echo('No account matching entered criteria found.')
	
	for account in to_be_untracked:
		if not click.confirm('Are you sure you want to untrack the {} account {}?'.format(account.REGISTRAR_NAME, account.identifier)):
			to_be_untracked.remove(account)
	manager.delete_accounts(*to_be_untracked)
	save_manager(manager)
	click.echo('Accounts untracked.')


@accounts.command('tag')
@click.option('-t', '--tags', help='Comma separated tag list.')
@click.option('-r', '--registrars', help='Specify accounts of which registrar(s) to tag.')
@click.argument('criteria', nargs=-1)
def tag_accounts(tags, registrars, criteria):
	if not tags:
		return click.echo('No tags specified.')
	if not criteria and not click.confirm('No criteria specified, will tag all accounts. Continue?'):
		return
	tags = tags.split(',')
	registrars = registrars and registrars.split(',') or []
	load_manager(manager, net_init=False)
	accounts = manager.get_accounts(registrars=registrars, criteria=criteria)
	for account in accounts:
		for tag in tags:
			if tag not in account.tags:
				account.tags.append(tag)
		click.echo('Tagged account {}'.format(account.unique_identifier))
	save_manager(manager)


@accounts.command('untag')
@click.option('-t', '--tags', help='Comma separated tag list.')
@click.option('-r', '--registrars', help='Specify accounts of which registrar(s) to untag.')
@click.argument('criteria', nargs=-1, required=True)
def untag_accounts(tags, registrars, criteria):
	if not tags:
		return click.echo('No tags specified.')
	tags = tags.split(',')
	registrars = registrars and registrars.split(',') or []
	load_manager(manager, net_init=False)
	accounts = manager.get_accounts(registrars=registrars, criteria=criteria)
	for account in accounts:
		for tag in tags:
			if tag in account.tags:
				account.tags.remove(tag)
		click.echo('Untagged account {}'.format(account.unique_identifier))
	save_manager(manager)



@accounts.command('update')
def update_account():
	pass


if __name__ == '__main__':
	cli()

