from pathlib import Path
import toml
import click
from tabulate import tabulate
from ohmydomains.manager import Manager
from ohmydomains.domain import Domain
from ohmydomains.registrars import registrars
from .registrars import registrar_cli_modifiers


CONFIG_PATH = Path.home().joinpath('.config', 'ohmydomains.toml')
CACHE_PATH = CONFIG_PATH.parent.joinpath('ohmydomains_cache.toml')


def load_config():
	return toml.loads(CONFIG_PATH.read_text())


def save_config(data):
	CONFIG_PATH.write_text(toml.dumps(data))


def load_cache():
	return toml.loads(CACHE_PATH.read_text())


def save_cache(data):
	CACHE_PATH.write_text(toml.dumps(data))


def load_manager(manager, net_init=True):
	data = load_config()
	manager.add_accounts((registrars[record['registrar']].Account(net_init=net_init, **record['credentials']) for record in data['accounts']))
	manager.add_domains(*data['raw_domains'])


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


@cli.command('list')
def list_domains():
	'''List domain names in tracked accounts and manually tracked ones.'''

	load_manager(manager)
	domains = []
	for account in manager.accounts:
		domains.extend(account.get_domains())
	click.echo(tabulate(((domain[k] for k in Domain.FIELDS) for domain in domains), headers=Domain.FIELDS))


@cli.group()
def accounts(): pass


LIST_ACCOUNTS_HEADER = ('registrar', 'credentials')
@accounts.command('list', help='List or search accounts.')
def list_accounts():
	load_manager(manager, net_init=False)
	table = ((account.REGISTRAR_NAME, ', '.join('{}={}'.format(k, v) for k, v in account._credentials.items())) for account in manager.accounts)
	click.echo(tabulate(table, headers=LIST_ACCOUNTS_HEADER))


@accounts.command('track', help='''Track a registrar account.
Enter credentials in the form of pairs of KEY:VALUE, which vary by registrar.
''')
@click.argument('registrar', required=True)
@click.argument('credentials', nargs=-1)
def track_account(registrar, credentials):
	if registrar not in registrars:
		click.echo('Registrar {} is not supported yet. Sorry.'.format(registrar))
		return
	
	if registrar in registrar_cli_modifiers:
		registrar_track_account = getattr(registrar_cli_modifiers[registrar], 'track_account', None)
		if registrar_track_account:
			try:
				account = registrar_track_account(credentials)
				load_manager(manager)
				manager.add_accounts(account)
				save_manager(manager)
				click.echo('Account tracked.')
				return
			except:
				click.echo('Failed tracking account. Please check and try again.')
				
	registrar = registrars[registrar]
	
	if credentials:	
		try:
			credentials = { pair[0]: pair[1] for pair in (kv.split(':') for kv in credentials) }
		except:
			click.echo('Invalid input. Please enter as prompted.')
			return
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
		load_manager(manager)
		manager.add_accounts(account)
		save_manager(manager)
		click.echo('Account tracked.')
	except:
		click.echo('Failed tracking account. Please check and try again.')


@accounts.command('untrack')
@click.argument('criteria', nargs=-1, required=True)
def untrack_accounts(criteria):
	load_manager(manager)
	to_be_untracked = manager.get_accounts(criteria=criteria)
	if not to_be_untracked:
		click.echo('No account matching entered criteria found.')
		return
	
	for account in to_be_untracked:
		prompt = 'Are you sure you want to untrack the {} account with credentials '.format(account.REGISTRAR_NAME)
		prompt += ', '.join('{}={}'.format(k, v) for k, v in account._credentials.items())
		if not click.prompt(prompt):
			to_be_untracked.remove(account)
	manager.delete_accounts(*to_be_untracked)
	save_manager(manager)
	click.echo('Accounts untracked.')


@accounts.command('update')
def update_account():
	pass


if __name__ == '__main__':
	cli()

