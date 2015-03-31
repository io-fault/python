import sys
from .. import library
from .. import tzif
from .. import libzone

def main():
	default = libzone.Zone.open(lambda x: library.Timestamp.of(unix=x), tzif.tzdefault)
	for transition, offset in zip(default.times, default.zones):
		sys.stdout.write("%s: %s\n" %(transition.select('iso'), offset))

if __name__ == '__main__':
	main()
