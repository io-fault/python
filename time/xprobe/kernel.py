import sys

platform = sys.platform.lower()

timelibs = {
	'linux': 'rt',
}

def initialize(context):
	with context as xact:
		if platform in timelibs:
			xact.dynamic_link(timelibs[platform])
