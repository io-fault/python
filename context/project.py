identity = 'http://fault.io/python/context'
name = 'context'
abstract = 'Context package for the fault.io core Python projects'
icon = '<http://fault.io>'

fork = 'foundation'
versioning = 'continuous'
status = 'flux'

controller = 'fault.io'
contact = 'mailto:critical@fault.io'

root = 'http://fault.io/python/'

projects = (
	'routes',
	'chronometry',
	'computation',
	'filesystem',
	'text',

	'development',
	'llvm',
	'factors',

	'cryptography',
	'traffic',
	'system',
	'interface',

	'internet',
	'io',
	'xml',
	'web',

	'terminal',
	'console',
)

if __name__ == '__main__':
	print('\n'.join(projects))
