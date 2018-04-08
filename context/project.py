identity = 'http://fault.io/src/python/context'
name = 'context'
abstract = 'Core project space'
icon = '🔋'

fork = 'potential'
versioning = 'continuous'
status = 'flux'

controller = 'fault.io'
contact = 'mailto:critical@fault.io'

root = 'http://fault.io/src/'

projects = [
	'computation',
	'chronometry', # rename to time
	'cryptography', # rename to security

	'daemon',
	'filesystem',

	'io',
	'internet',
	'sectors',

	'routes',
	'syntax',
	'system',
	'terminal',
	'text',
	'traffic',

	'web',
	'xml',
]

if __name__ == '__main__':
	print('\n'.join(projects))
