"""
# Repeatedly print the current date and time every 64 milliseconds.

# Carriage returns will be used to overwrite previous displays.
"""
import sys
from .. import library

def print_local_timestamp(clock = library.clock):
	localtime = library.zone()
	try:
		for total in clock.meter(delay=library.Measure.of(millisecond=64)):
			ts = clock.demotic()
			st = localtime.localize(ts)[0].select('iso')
			sys.stdout.write(("   " + st + "\r"))
	except KeyboardInterrupt:
		sys.stdout.write("\r\n")
		sys.exit(0)

if __name__ == '__main__':
	print_local_timestamp()
