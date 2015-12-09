"""
Gregorian calendar functions and data.
"""
import operator
from . import calendar as callib

#: number of centuries in a gregorian cycle.
centuries_in_cycle = 4

#: number of years in a century.
years_in_century = 100

#: number of years in a decade
years_in_decade = 10

#: number of centuries in a millennium
centuries_in_millennium = 10

#: english names of the months of the year.
month_names = (
	"january",
	"february",
	"march",
	"april",
	"may",
	"june",
	"july",
	"august",
	"september",
	"october",
	"november",
	"december",
)

#: number of months in a year.
months_in_year = len(month_names)

#: abbreviations for the english names of the months of the year.
month_abbreviations = (
	"jan", "feb", "mar",
	"apr", "may", "jun",
	"jul", "aug", "sep",
	"oct", "nov", "dec",
)

#: Finite map associating the names and abbreviations of the months with a zero-based index.
month_name_to_number = {
	month_names[i] : i for i in range(len(month_names))
}
month_name_to_number.update([
	(k[:3], v) for (k,v) in month_name_to_number.items()
])

#: Definition of a year in terms of gregorian month-to-days.
calendar_year = (
	31, 28, 31, 30,
	31, 30, 31, 31,
	30, 31, 30, 31
)

#: Definition of a leap year in terms of gregorian month-to-days.
calendar_leap = (calendar_year[0], calendar_year[1] + 1) + calendar_year[2:] # Feb29

### Gregorian Cycle
# After calculation, nodes take the form:
# (title, multiplier, total_months, total_days, sub)
leap_cycle = (
	('leap', 1, calendar_leap),
	('years', 3, calendar_year)
)

cycle = (
	'gregorian-cycle', 1, (
		# First century; normal leap cycle throughout.
		('first-century', 25, leap_cycle),

		# Subsequent three centuries in the cycle.
		# First year in century is leap exception.
		('centuries', 3, (
			('first-year-exception', 4, calendar_year),
			('regular-cycle', 24, leap_cycle),
		)),
	)
)

calendar = callib.aggregate(cycle)

def resolve_by_months(months,
	_select_months = operator.itemgetter(0),
	_select_days = operator.itemgetter(1),
	_calendar = calendar,
):
	return callib.resolve((_select_months, _select_days), months, _calendar)

def resolve_by_days(days,
	_select_months = operator.itemgetter(0),
	_select_days = operator.itemgetter(1),
	_calendar = calendar,
):
	return callib.resolve((_select_days, _select_months), days, _calendar)

#: Total number of months in a Gregorian cycle.
months_in_cycle = months_in_year * years_in_century * centuries_in_cycle

# Find the number of days in the cycle using the resolve function.
r = resolve_by_months(months_in_cycle-1)
days_in_cycle = r[1] + r[-1]

def year_is_leap(y):
	"""
	Given a gregorian calendar year, determine whether it is a leap year.
	"""
	if y % 4 == 0 and (y % 400 == 0 or not y % 100 == 0):
		return True
	return False

def month_from_days(days, _resolver = resolve_by_days):
	"""
	Convert the given number Earth-days to a month in the Gregorian cycle.

	! NOTE:
		This does not communicate the remainder of days.
	"""
	cycles, months, day, _d = _resolver(days)
	return ((cycles * 400 * 12) + months)

def days_from_month(months, _resolver=resolve_by_months):
	"""
	Convert the given months to the number of Earth-days leading up to the
	Gregorian month.
	"""
	cycles, day_of_cycle, moy, _d = _resolver(months)
	return (cycles * days_in_cycle) + day_of_cycle

def date_from_days(days, _resolver=resolve_by_days):
	"""
	Convert the given Earth-days into a Gregorian date in the common form:
	 (year, month, day).
	"""
	cycles, months, day, _d = _resolver(days)
	year_of_cycle, moy = divmod(months, months_in_year)
	return ((cycles * 400) + year_of_cycle, moy + 1, day + 1)

def days_from_date(date, _resolver=resolve_by_months):
	"""
	Convert a Gregorian date in the common form, (year, month, day), to the number
	of days leading up to the date.
	"""
	year, month, day = date
	month -= 1
	day -= 1
	cycles, day_of_cycle, moy, _d = _resolver(month + (year * 12))
	return (cycles * days_in_cycle) + day_of_cycle + day

def context(context):
	import fractions
	# Defines
	context.define('year', 'month', 1, fractions.Fraction(months_in_year,1))
	context.define('century', 'year', 1, fractions.Fraction(years_in_century,1))
	context.define('gregorian', 'year', 1, fractions.Fraction(400,1))
	context.define('decade', 'year', 1, fractions.Fraction(years_in_decade,1))
	context.define('millennium', 'century', 1,
		fractions.Fraction(centuries_in_millennium,1))

	# Bridges
	context.bridge('month', 'day', days_from_month)
	context.bridge('day', 'month', month_from_days)

	# Containers
	def unpack_date_tuple(typ, date):
		return (('day', days_from_date(date)),)
	def pack_date_tuple(time, arg):
		return date_from_days(time.select('day'))
	context.container('date', pack_date_tuple, unpack_date_tuple)

	def unpack_datetime_tuple(typ, time):
		return (('date', time[:3]), ('timeofday', time[3:6]))
	def pack_datetime_tuple(time, arg):
		return time.select('date') + time.select('timeofday')
	context.container('datetime', pack_datetime_tuple, unpack_datetime_tuple)
