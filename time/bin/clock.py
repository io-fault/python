import sys
from .. import library

def main(clock = library.clock):
	localtime = library.zone()
	try:
		for total in clock.meter(centisecond=4):
			ts = clock.demotic()
			st = localtime.localize(ts)[0].select('iso')
			sys.stdout.write(("   " + st + "\r"))
	except KeyboardInterrupt:
		sys.stdout.write("\r\n")
		sys.exit(0)

if __name__ == '__main__':
	main()
