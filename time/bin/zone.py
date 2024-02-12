import sys
from .. import types
from .. import tzif
from .. import views

def print_zone_transitions():
	default = views.Zone.open(types.from_unix_timestamp, tzif.tzdefault)
	for transition, offset in zip(default.transitions, default.offsets):
		sys.stdout.write("%s: %s\n" %(transition.select('iso'), offset))

if __name__ == '__main__':
	print_zone_transitions()
