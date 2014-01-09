import sys

def probe(context):
	if sys.platform.lower() == 'linux':
		context._dynamic_link(('rt',))
