"""
# Week based measures of time: days of seven.
"""
#: English names of the days of the week.
weekday_names = (
	'sunday',
	'monday',
	'tuesday',
	'wednesday',
	'thursday',
	'friday',
	'saturday',
)

#: Total number of a days in a week.
days_in_week = len(weekday_names)

#: Total number of weeks in a fortnight
weeks_in_fortnight = 2

#: Abbreviations for the english names of the days of the week.
weekday_abbreviations = (
	'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat',
)

#: Map of weekday names and abbreviations from a zero-based index.
weekday_name_to_number = {
	weekday_names[i]: i
	for i in range(len(weekday_names))
}

#: Map of weekday names and abbreviations to a zero-based index.
weekday_name_to_number.update([
	(k[:3], v) for (k,v) in weekday_name_to_number.items()
])

def day_of_week(offset, days):
	"""
	# Derive the canonical day of week from the given offset and days.
	"""
	return ((days % 7) - offset) % 7

def week_from_days(offset, days):
	return (days - offset) // 7

def days_from_week(offset, weeks):
	return (weeks * 7) + offset

def context(context):
	import fractions
	# Datum Week. Given a situation where the Datum changes to a non-Sunday point,
	# Some significant changes will need to be made in order to continue supporting
	# day of week updates.
	context.define('week', 'day', 1, base = fractions.Fraction(days_in_week, 1))
	context.define('fortnight', 'week', 1, base = fractions.Fraction(weeks_in_fortnight, 1))

	# Containers
	def unpack_weekday(pit, of = None, weekday_names = weekday_names):
		return weekday_names[pit.select('day', 'week')]
	context.container('weekday', unpack_weekday, None)
