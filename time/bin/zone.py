import sys
from .. import library
from .. import tzif
from .. import views

def print_zone_transitions():
	default = views.Zone.open(lambda x: library.Timestamp.of(unix=x), tzif.tzdefault)
	for transition, offset in zip(default.transitions, default.offsets):
		sys.stdout.write("%s: %s\n" %(transition.select('iso'), offset))

if __name__ == '__main__':
	print_zone_transitions()
