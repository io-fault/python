"""
# Format and parse datetime strings.

# Primarily this module exposes two functions: &parser,
# &formatter. These functions provide access to datetime formats defined by a
# standard or deemed common enough to merit a builtin implementation.

# ! NOTE:
	# Currently does not provide access to strptime and strftime functionality.

# While formatting PiTs can usually occur without error, parsing them from strings
# can result in a variety of errors. The parsers available in
# libformat can raise subclasses of &.core.FormatError.
"""
import operator
import functools
import fractions # For arbitrary subsecond representations.
import math

from . import core
from . import gregorian
from . import week

rfc1123 = "{day_of_week}, {day:02} {month} {year} {hour:02}:{minute:02}:{second:02}"
iso8601 = "{0}-{1:02}-{2:02}T{3:02}:{4:02}:{5:02}.{6}"

models = {
	'rfc1123' : rfc1123,
	'iso8601' : iso8601,
}

def parse_rfc1123(s,
	abbrev_to_month = gregorian.month_abbreviations.__getitem__,
	len = len
):
	# be loose with the comma; don't break
	# if there's whitespace between the DOW and comma.
	comma = s.find(',')
	if comma == -1:
		raise ValueError('comma not found')
	day_of_week = s[:comma].strip()
	fields = s[comma+1:].strip().split()
	trail = fields[4:]
	day, month, year, time = fields[:4]
	hour, minute, second = time.split(':')

	timezone = None
	if trail:
		if len(trail) > 1:
			raise ValueError('unexpected data at end of string')
		timezone = trail[0]
	return (
		('day_of_week', day_of_week),
		('year', year),
		('month', month),
		('day', day),
		('hour', hour),
		('minute', minute),
		('second', second),
		('timezone', timezone)
	)

def parse_iso8601(s, mstrip = operator.methodcaller('strip')):
	s = s.lower()
	if 't' in s:
		date, time = s.split('t', 1)
	else:
		date = s
		time = ''
	offset = ''

	if not time:
		hour = '0'
		minute = '0'
		second = '0'
		subsecond = '0'
		zone = ('0','0')
	else:
		# be sure to process the zone from the end.
		if time.endswith('z'):
			time = time[:-1]
			zone = '0:0'
		elif '+' in time:
			time, zone = time.rsplit('+', 1)
		elif '-' in time:
			_time, zone = time.rsplit('-', 1)
			# cover cases like: 10:-24.2340
			if ':' not in _time or ':' not in zone:
				zone = '0:0'
			else:
				# transform adds the minute/second of the offset to the
				# hour/minute field.
				offset = '-'
				time = _time
		else:
			zone = '0:0'
		zone = zone.split(':', 1)
		if '.' in time:
			hm, subsecond = time.rsplit('.', 1)
		else:
			# no subseconds
			hm = time
			subsecond = '0'
		hour, minute, second = hm.split(':', 2)
	date = zip(('year', 'month', 'day'), map(mstrip, date.rsplit('-', 2)))
	return tuple(date) + (
		('hour', hour),
		('minute', minute),
		('second', second),
		('subsecond', subsecond),
		('timezone', zone),
		('offset', offset),
	)

parsers = {
	'rfc1123': parse_rfc1123,
	'iso8601': parse_iso8601,
}

def transform_iso8601(args,
	get1 = operator.itemgetter(1),
	Fraction = fractions.Fraction
):
	struct = args[1]
	tzh, tzm = (struct['offset'] + x for x in struct['timezone'])
	return args + (
		(
			(
				int(struct['year']),
				int(struct['month']),
				int(struct['day']),
				int(struct['hour']) + int(tzh),
				int(struct['minute']) + int(tzm),
				int(struct['second']),
				Fraction(int(struct['subsecond']), 10**(len(struct['subsecond']))),
			),
		),
	)

def transform_rfc1123(args, int = int):
	struct = args[1]
	month = gregorian.month_name_to_number[struct['month'].lower()]
	return args + (
		(
			(
				int(struct['year']),
				month + 1, # for consistency with ISO.
				int(struct['day']),
				int(struct['hour']),
				int(struct['minute']),
				int(struct['second']),
				0, # no subsecond
			),
		),
	)

transformers = {
	'iso8601' : transform_iso8601,
	'rfc1123' : transform_rfc1123,
}

def validate_rfc1123(args, weekdays = week.weekday_name_to_number):
	# check the integrity of the parse rfc1123 timestamp
	src, struct, tup = args

	if struct['timezone'].strip().lower() not in ('zulu', 'z', 'gmt', 'utc'):
		raise ValueError("timezone not GMT")

	dow = struct['day_of_week'].lower()
	if dow not in weekdays:
		raise ValueError("invalid day of week: " + dow)
	dow = weekdays[dow]

	return tup

validators = {
	'rfc1123': validate_rfc1123,
}

aliases = {'http' : 'rfc1123'}

def _parse(fun, format):
	def EXCEPTION(src, fun = fun, format = format):
		try:
			return (src, dict(fun(src)))
		except core.ParseError:
			raise
		except Exception as e:
			parse_error = core.ParseError(src, format = format)
			parse_error.__cause__ = e
			raise parse_error
	functools.update_wrapper(EXCEPTION, fun)
	return EXCEPTION

def _structure(fun, format):
	def EXCEPTION(state):
		try:
			return fun(state)
		except core.StructureError:
			raise
		except Exception as e:
			struct_error = core.StructureError(*state, format = format)
			struct_error.__cause__ = e
			raise struct_error
	functools.update_wrapper(EXCEPTION, fun)
	return EXCEPTION

def _integrity(fun, format):
	def EXCEPTION(state):
		try:
			return fun(state)
		except core.IntegrityError:
			raise
		except Exception as e:
			integ_error = core.IntegrityError(*state, format = format)
			integ_error.__cause__ = e
			raise integ_error
	functools.update_wrapper(EXCEPTION, fun)
	return EXCEPTION

def parser(fmt, _deref = aliases.get, _getn1 = operator.itemgetter(-1)):
	"""
	# Given a format idenifier, return the function that can be used to parse
	# the formatted string into a Point instance.
	"""
	fmt = _deref(fmt, fmt)
	def parser_composition(
		x,
		integ = _integrity(validators.get(fmt, _getn1), fmt),
		struct = _structure(transformers[fmt], fmt),
		parse = _parse(parsers[fmt], fmt),
	):
		return integ(struct(parse(x)))[0]
	return parser_composition

def format_rfc1123(pitt, subsec, dow, _fmt = models['rfc1123'].format,
	month_abbrev = gregorian.month_abbreviations.__getitem__,
	dow_abbrev = week.weekday_abbreviations.__getitem__,
):
	y, m, d, h, min, s = pitt

	return _fmt(
		year = y, month = month_abbrev(m-1).capitalize(), day = d,
		hour = h, minute = min, second = s,
		day_of_week = dow_abbrev(dow).capitalize(),
		timezone = 'GMT'
	)

def format_iso8601(pitt, subsec, dow,
	_fmt = models['iso8601'].format, log = math.log10, str = str
):
	sub = str(subsec[0])
	# justify according to precision
	sub = sub.rjust(int(log(subsec[1])), "0")
	# strip trailing zeros for conciseness repr
	sub = sub.rstrip("0")
	return _fmt(*(pitt + (sub or "0",)))

formatters = {
	'rfc1123' : format_rfc1123,
	'iso8601' : format_iso8601,
}

def formatter(fmt, _deref = aliases.get):
	"""
	# Given a format idenifier, return the function that can be used to format
	# the Point in time.
	"""
	return formatters[_deref(fmt, fmt)]

formats = {
	'iso' : 'iso8601',
	'rfc' : 'rfc1123',
}

def context(context):
	for k, id in formats.items():
		fmt = formatter(id)
		par = parser(id)
		def unpack_and_format(x, arg, fmt = fmt):
			sub = (x.select(x.unit, 'second'), x.context.convert('second', x.unit, 1))
			return fmt(x.select('datetime'), sub, x.select('day', 'week'))
		def parse_and_unpack(typ, txt, par = par):
			*datetime, subsec = par(txt)
			return [('datetime', datetime), ('subsecond', subsec)]
		context.container(k, unpack_and_format, parse_and_unpack)
