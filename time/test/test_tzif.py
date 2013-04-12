import os
import os.path
from .. import tzif

def test_loadall(test, _join = os.path.join, bytes = bytes, bool = bool, int = int):
	return
	# load all the TZif files in the tzdir(/usr/share/zoneinfo).
	for dirpath, dirname, filenames in os.walk(tzif.tzdir):
		for x in filenames:
			tzname = _join(dirpath, x)
			tz = tzif.get_timezone_data(tzname)

			if tz is not None:
				zones, tt, leap = tz

				for y in tt:
					test/2 == len(y)
					tt, tz = y
					test/tt / int
					test/tz.tz_abbrev / bytes
					test/tz.tz_offset / int
					test/tz.tz_isdst / bool
					test/tz.tz_isstd / bool
					test/tz.tz_isgmt / bool
