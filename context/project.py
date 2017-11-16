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

projects = (
	'chronometry',
	'computation',
	'console',
	'cryptography',

	'development',
	'factors',
	'filesystem',

	'io',
	'internet',
	'daemon',

	'routes',
	'stack',
	'system',
	'terminal',
	'text',
	'traffic',

	'web',
	'xml',
)

if __name__ == '__main__':
	print('\n'.join(projects))
