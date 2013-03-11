import sys
from .. import lib
from .. import tzif
from .. import libzone

def main():
	default = libzone.Zone.open(lambda x: lib.Timestamp.of(unix=x), tzif.tzdefault)
	for transition, offset in zip(default.times, default.zones):
		sys.stdout.write("%s: %s\n" %(transition.select('iso'), offset))

if __name__ == '__main__':
	main()
