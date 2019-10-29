from setuptools import setup


setup(
	name='ohmydomains',
	version=open('CHANGELOG').readline().replace('\n', ''),

	packages=['ohmydomains'],
	install_requires=[
		'requests',
		'pendulum',
		'toml',
		'click',
		'tabulate'
	],

	entry_points='''
		[console_scripts]
		omd=cli.cli:cli
	'''
)

