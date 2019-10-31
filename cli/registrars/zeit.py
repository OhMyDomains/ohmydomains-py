import click
import requests
from ohmydomains.registrars.zeit import ZeitAccount


def track_account(*args, **kwargs):
	click.echo('We will now follow the authentication flow of ZEIT.')
	email = click.prompt('Please enter your email')
	init = requests.post(ZeitAccount.API_BASE + '/now/registration', json={
		'email': email,
		'tokenName': 'OhMyDomains CLI'
	}).json()
	click.echo('ZEIT will now send to you a confirmation email with the code: ', newline=False)
	click.echo(init['securityCode'])
	click.echo('Please confirm it, and press enter.', nl=False)
	input()
	verify = requests.get(ZeitAccount.API_BASE + '/now/registration/verify', params={
		'email': email,
		'token': init['token']
	}).json()
	print(verify)
	return ZeitAccount(email=email, token=verify['token'])

