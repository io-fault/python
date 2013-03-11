##
# .test.test_tzif
##
import os
import os.path
from .. import tzif

def test_loadall(test, _join = os.path.join, bytes = bytes, bool = bool, int = int):
	# load all the TZif files in the tzdir(/usr/share/zoneinfo).
	for dirpath, dirname, filenames in os.walk(tzif.tzdir):
		for x in filenames:
			tzname = _join(dirpath, x)
			tz = tzif.get_timezone_data(tzname)
			if tz is not None:
				zones, tt, leap = tz
				for y in tt:
					test.fail_if_not_equal(2, len(y))
					tt, tz = y
					test.fail_if_not_instance(tt, int)
					test.fail_if_not_instance(tz.tz_abbrev, bytes)
					test.fail_if_not_instance(tz.tz_offset, int)
					test.fail_if_not_instance(tz.tz_isdst, bool)
					test.fail_if_not_instance(tz.tz_isstd, bool)
					test.fail_if_not_instance(tz.tz_isgmt, bool)

if __name__ == '__main__':
	from dev import libtest; libtest.execmodule()
