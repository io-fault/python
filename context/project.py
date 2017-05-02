identity = 'http://code.fault.io/fault.context'
name = 'context'
abstract = 'Context package for the fault.io intersection projects'
icon = '<http://fault.io>'

fork = 'foundation'
versioning = 'continuous'
status = 'flux'

controller = 'fault.io'
contact = 'mailto:critical@fault.io'

root = 'http://fault.io/python/'

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
	'llvm',

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
