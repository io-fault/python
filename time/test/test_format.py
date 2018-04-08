from .. import core
from .. import format as module

samples = [
	('negative_year', (
		(-800, 1, 1, 0, 0, 0, 0), (
			('rfc1123', "Sat, 1 Jan -800 00:00:00 GMT"),
			('iso8601', "-800-01-01T00:0:0.0Z"),
		)
	)),
	('slight_cycle_offset', (
		(2010, 7, 16, 2, 32, 39, 0), (
			('rfc1123', "Fri, 16 Jul 2010 02:32:39 GMT"),
			('iso8601', "2010-07-16T02:32:39.0Z"),
		)
	)),
	('cycle_aligned', (
		(1600, 1, 1, 0, 0, 0, 0), (
			('rfc1123', "Sat, 1 Jan 1600 00:00:00 GMT"),
			('iso8601', "1600-1-1T0:0:0Z"),
		)
	)),
	('first_century', (
		(1300, 1, 1, 0, 0, 0, 0), (
			('rfc1123', "Fri, 1 Jan 1300 00:00:00 GMT"),
			('iso8601', "1300-01-01T00:0:0.0Z"),
		)
	)),
	# iso8601 allows for offsets to be defined.
	# make sure that the timezone offsets get properly applied.
	('iso_tz_offset', (
		(2000, 1, 1, 10, 0, 0, 0), (
			('iso8601', '2000-01-01T04:00:00.0+06:00'),
			('iso8601', '2000-01-01T16:00:00.0-06:00'),
			('iso8601', '2000-01-01T20:30:00.0-10:30'),
			# no subseconds
			('iso8601', '2000-01-01T10:30:00-00:30'),
			('iso8601', '2000-01-01T04:00:00+06:00'),
			('iso8601', '2000-01-01T16:00:00-06:00'),
			('iso8601', '2000-01-01T20:30:00-10:30'),
		)
	)),
	('iso_tz_offset_mins', (
		(2000, 1, 1, 9, 60, 0, 0), (
			('iso8601', '2000-01-01T09:30:00.0+00:30'),
			#('iso8601', '2000-01-00T9:30:00.0+24:30'),
			# no subseconds
			('iso8601', '2000-01-01T09:30:00+00:30'),
			#('iso8601', '2000-01-00T9:30:00+24:30'),
		)
	)),
]

exceptional_samples = [
	('iso8601', (
		(core.ParseError, (
			123, # not a string
			None, # not a string
		)),
		(core.StructureError, (
			"2000-01-01T5:30:0-0A:00", # "0A" not an integer
			"Tue, 16 Jul 2010 02:32:39 GMT", # inappropriate format
		)),
		(core.IntegrityError, (
			# no integrity checks performed by iso8601
		)),
	)),
	('rfc1123', (
		(core.ParseError, (
			123, # not a string
			None, # not a string
		)),
		(core.StructureError, (
			"Fri, 16 Jel 2010 02:32:39 GMT", # can't structure with invalid month name
		)),
		(core.IntegrityError, (
			#"Tue, 16 Jul 2010 02:32:39 GMT", invalid weekday
			"Fri, 16 Jul 2010 02:32:39 PCT",
		)),
	)),
]

def test_samples(test):
	for title, (pit_tuple, pit_formats) in samples:
		for format, val in pit_formats:
			parser = module.parser(format)
			test_pit = tuple(parser(val))
			test/test_pit == pit_tuple

def test_errors(test):
	for format, errors in exceptional_samples:
		parser = module.parser(format)
		for error, samples in errors:
			for x in samples:
				with test/error as exc:
					parser(x)

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
