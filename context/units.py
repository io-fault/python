"""
# Information units for human readable sizes.
"""
import bisect

formatting = "{0:0<5.4} {1}"

orders = {
	0: ('', ''),
	1: ('kilo', 'kibi'),
	2: ('mega', 'mebi'),
	3: ('giga', 'gibi'),
	4: ('tera', 'tebi'),
	5: ('peta', 'pebi'),
	6: ('exa', 'exbi'),
	7: ('zetta', 'zebi'),
	8: ('yotta', 'yobi'),
}

_metric = (1000, [
	1000 ** o for o in orders
])

_iec = (1024, [
	1024 ** o for o in orders
])

def identify(boundary, size, search=bisect.bisect):
	index = max(min(search(boundary[1], abs(size))-1, 8), 0)
	return (size / (boundary[0] ** index), index)

def metric(size):
	units, order = identify(_metric, size)
	return (units, order, orders[order][0])

def iec(size):
	units, order = identify(_iec, size)
	return (units, order, orders[order][1])

def format_metric(size):
	units, order, label = metric(size)
	o = label[:1].upper()

	if o:
		o += "B"
	else:
		o = "bytes"

	return formatting.format(units, o)

def format_iec(size):
	units, order, label = iec(size)
	o = label[:1].upper()

	if o:
		o += "iB"
	else:
		o = "bytes"

	return formatting.format(units, o)
