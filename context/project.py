identity = 'http://fault.io/src/fault.context'
name = 'context'
abstract = 'Context package for the fault.io intersection projects'
icon = '🔋'

fork = 'potential'
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
	'python',

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
