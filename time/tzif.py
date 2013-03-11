"""
Read TZif, time zone information, files(zic output).

.. warning:: This module is intended for internal use only. The protocol is subject to change without warning.
"""
import os
import os.path
import struct
import collections

magic = b'TZif'
tzdir = '/usr/share/zoneinfo'
tzdefault = '/etc/localtime'
tzenviron = 'TZ'

header_fields = (
	'tzh_ttisgmtcnt',  # The number of UTC/local indicators stored in the file.
	'tzh_ttisstdcnt',  # The number of standard/wall indicators stored in the file.
	'tzh_leapcnt',     # The number of leap seconds for which data is stored in the file.
	'tzh_timecnt',     # The number of ``transition times'' for which data is stored in the file.
	'tzh_typecnt',     # The number of ``local time types'' for which data is stored in the file (must not be zero).
	'tzh_charcnt',     # The number of characters of ``time zone abbreviation strings'' stored in the file.
)
tzinfo_header = collections.namedtuple('tzinfo_header', header_fields)
header_struct_v1 = struct.Struct("!" + (len(header_fields) * "l"))
header_struct_v2 = struct.Struct("!" + (len(header_fields) * "q"))

ttinfo_fields = (
	'tt_gmtoff',
	'tt_isdst',
	'tt_abbrind',
)
tzinfo_ttinfo = collections.namedtuple('tzinfo_ttinfo', ttinfo_fields)
ttinfo_struct_v1 = struct.Struct("!lbb")
ttinfo_struct_v2 = struct.Struct("!qbb")

transtime_struct_v1 = struct.Struct("!l")
leappairs_struct_v1 = struct.Struct("!ll")

transtime_struct_v2 = struct.Struct("!q")
leappairs_struct_v2 = struct.Struct("!qq")

tzinfo = collections.namedtuple('tzinfo', (
	'header',
	'transitional_times',
	'types',
	'typinfo'
))

def parse_version_1(data):
	"""
	parse the raw data from a TZif file. 4-byte longs.

	Returns tuple of: (transtimes, types, timetypinfo, leaps, isstd, isgmt, abbr)
	See tzfile(5) for information about the fields(it's cryptically fun).
	"""
	x = data[:header_struct_v1.size]
	y = data[header_struct_v1.size:]
	header = tzinfo_header(*header_struct_v1.unpack(x))

	end = header.tzh_timecnt * 4
	size = transtime_struct_v1.size
	transtimes = tuple([
		transtime_struct_v1.unpack(y[x:x+size])[0]
		for x in range(0, end, size)
	])
	y = y[end:]

	# unsigned char's
	types = tuple(bytes(y[:header.tzh_timecnt]))
	y = y[header.tzh_timecnt:]

	end = ttinfo_struct_v1.size * header.tzh_typecnt
	timetypinfo = [
		tzinfo_ttinfo(*ttinfo_struct_v1.unpack(y[x:x+ttinfo_struct_v1.size]))
		for x in range(0, end, ttinfo_struct_v1.size)
	]
	y = y[end:]

	end = leappairs_struct_v1.size * header.tzh_leapcnt
	leaps = tuple([
		leappairs_struct_v1.unpack(y[x:x+leappairs.size])
		for x in range(0, end, leappairs_struct_v1.size)
	])
	y = y[end:]

	abbr = bytes(y[:header.tzh_charcnt])
	y = y[header.tzh_charcnt:]

	isstd = tuple(bytes(y[:header.tzh_ttisstdcnt]))
	y = y[header.tzh_ttisstdcnt:]

	isgmt = tuple(bytes(y[:header.tzh_ttisgmtcnt]))
	y = y[header.tzh_ttisgmtcnt:]

	##
	# Resolve the abbrind. Append a NUL terminator to the
	# string to guarantee that abbr.find() will not return -1.
	abbr += b'\0'
	timeinfo = tuple([
		(abbr[x.tt_abbrind:abbr.find(b'\0', x.tt_abbrind)], x.tt_gmtoff, x.tt_isdst)
		for x in timetypinfo
	])

	return (transtimes, types, leaps, isstd, isgmt, timeinfo)

def parse_version_2(data):
	"""
	parse the raw data from a version 2 TZif file. 8-byte longs.

	Returns tuple of: (transtimes, types, timetypinfo, leaps, isstd, isgmt, abbr)
	See tzfile(5) for information about the fields(it's cryptically fun).
	"""
	x = data[:header_struct_v2.size]
	y = data[header_struct_v2.size:]
	header = tzinfo_header(*header_struct_v2.unpack(x))

	end = header.tzh_timecnt * 4
	size = transtime_struct_v2.size
	transtimes = tuple([
		transtime_struct_v2.unpack(y[x:x+size])[0]
		for x in range(0, end, size)
	])
	y = y[end:]

	# unsigned char's
	types = tuple(bytes(y[:header.tzh_timecnt]))
	y = y[header.tzh_timecnt:]

	end = ttinfo_struct_v2.size * header.tzh_typecnt
	timetypinfo = [
		tzinfo_ttinfo(*ttinfo_struct_v2.unpack(y[x:x+ttinfo_struct_v2.size]))
		for x in range(0, end, ttinfo_struct_v2.size)
	]
	y = y[end:]

	end = leappairs_struct_v2.size * header.tzh_leapcnt
	leaps = tuple([
		leappairs_struct_v2.unpack(y[x:x+leappairs.size])
		for x in range(0, end, leappairs_struct_v2.size)
	])
	y = y[end:]

	abbr = bytes(y[:header.tzh_charcnt])
	y = y[header.tzh_charcnt:]

	isstd = tuple(bytes(y[:header.tzh_ttisstdcnt]))
	y = y[header.tzh_ttisstdcnt:]

	isgmt = tuple(bytes(y[:header.tzh_ttisgmtcnt]))
	y = y[header.tzh_ttisgmtcnt:]

	##
	# Resolve the abbrind. Append a NUL terminator to the
	# string to guarantee that abbr.find() will not return -1.
	abbr += b'\0'
	timeinfo = tuple([
		(abbr[x.tt_abbrind:abbr.find(b'\0', x.tt_abbrind)], x.tt_gmtoff, x.tt_isdst)
		for x in timetypinfo
	])

	return (transtimes, types, leaps, isstd, isgmt, timeinfo)

def parse(data):
	"""
	Given TZif data, identify the appropriate version and unpack the timezone information.
	"""
	ident, data = (data[:20], data[20:])
	if ident[:4] != magic:
		# not a TZif file
		return None
	if ident[5] == b'2':
		return parse_version_2(data)
	else:
		return parse_version_1(data)

tzinfo = collections.namedtuple('tzinfo', (
	'tz_abbrev',
	'tz_offset',
	'tz_isdst',
	'tz_isstd',
	'tz_isgmt',
))
def structure(tzif):
	'given the parse fields from parse(), make a more accessible structure'
	(transtimes, types, leaps, isstd, isgmt, timeinfo) = tzif
	ltt = []
	i = -1
	for x in timeinfo:
		i += 1
		ttyp = tzinfo(
			tz_abbrev = x[0],
			tz_offset = x[1],
			tz_isdst = bool(x[2]),
			tz_isstd = bool(isstd[i]),
			tz_isgmt = bool(isgmt[i])
		)
		ltt.append(ttyp)

	r = list(zip(transtimes, map(ltt.__getitem__, types)))
	# order by the offset
	r.sort(key = lambda x: x[0])
	return tuple(ltt), r, leaps

def system_timezone_file(relativepath, tzdir = tzdir, _join = os.path.join):
	return _join(tzdir, relativepath)

def get_timezone_data(filepath):
	"""
	Get the structured timezone data out of the specified file.
	"""
	with open(filepath, 'rb') as f:
		d = parse(f.read())
		if d is None:
			return None
		return structure(d)

def abbreviations(tzdir, _join = os.path.join, bytes = bytes, bool = bool, int = int):
	"""
	abbreviations(tzdir)

	Yield all abbreviations in the TZif files in the tzdir(/usr/share/zoneinfo).
	"""
	prefixlen = len(libtzif.tzdir) + 1
	for dirpath, dirname, filenames in os.walk(libtzif.tzdir):
		for x in filenames:
			tzname = _join(dirpath, x)[prefixlen:]
			tz = libtzif.getdata(tzname)
			if tz is not None:
				zones, tt, leap = tz
				for tz in zones:
					yield (tz.tz_abbrev.decode('ascii'), tzname, tz.tz_offset, tz.tz_isdst)

def abbreviation_map(tzdir = tzdir):
	"""
	Generate and return a mapping of zone abbreviations to their particular offsets.

	Using this should mean that you know that abbreviations are ambiguous.
	This function is provided to aid common cases and popular mappings.
	"""
	a = set(abbreviations(tzdir))
	d = dict()
	for x in a:
		if x[1] not in d:
			d[x[1]] = set()
		d[x[1]].add((x[0], x[2], x[3]))
	d2 = dict()
	for (k, v) in d.items():
		for x in v:
			if x[0] not in d2:
				d2[x[0]] = set()
			d2[x[0]].add((k, x[1], x[2]))
	return d2

if __name__ == '__main__':
	import sys
	for x in sys.argv[1:]:
		f = open(x, 'rb').read()
		d = parse(memoryview(f))
		if d is None:
			sys.stderr.write('not a timezone information file: ' + x + '\n')
			sys.exit(1)
		zones, transt, leaps = structure(d)
		for x in transt:
			print(x)
		for x in zones:
			print(x)
	sys.exit(0)
