"""
Arbitrary Calendar Address Resolution

Used internally by &.gregorian in order to work with the gregorian calendar pattern.
"""
import itertools
import operator

##
# Calculate the total days and months needed by resolve().
def aggregate(node,
		chain=itertools.chain,
		accumulate=itertools.accumulate,
		isinstance=isinstance, int=int,
		tuple=tuple, range=range,
		len=len, sum=sum,
	):
	"""
	Recursively aggregate the data in the node.
	"""
	title, repeat, sub = node

	if isinstance(sub[0], int):
		# leaf
		day_accum = tuple(accumulate(chain((0,), sub)))
		month_accum = tuple(range(13)) # sub
		agg = (month_accum, day_accum)
		month_value = len(sub)
		day_value = day_accum[-1]
	else:
		# sequence of inner nodes
		#agg = tuple(map(aggregate, sub))
		agg = tuple([aggregate(x) for x in sub])
		month_value = sum([y[-1][0] for y in agg])
		day_value = sum([y[-1][1] for y in agg])

	# calculate the days consumed by the sub nodes
	return (
		title, repeat, agg,
		(month_value, day_value),
		(repeat * month_value, repeat * day_value),
	)

##
# Search an arbitrary calendar cycle for the appropriate address.
# Returns (address, remainder, difference) where
#  Address is the resolved address of days or months.
#  Remainder is the address quantity not consumed. (day of month)
#  Difference is the difference between final address part and the next. (days in month)

def resolve(selectors, iaddress, calendar,
		divmod=divmod, isinstance=isinstance,
		range=range, len=len, int=int,
	):
	sipart, sopart = selectors
	oaddress = 0 # current output address

	# align on a cycle
	cycles, iaddress = divmod(iaddress, sipart(calendar[-1]))

	current = calendar
	# Continue consuming the aggregates until a leaf.
	while not isinstance(current[2][0][0], int):
		for sub in current[2]:
			title, repeat, inner, fragments, totals = sub
			itotal = sipart(totals)
			if iaddress >= itotal:
				# Completely consumed. Continue to next node.
				iaddress -= itotal
				oaddress += sopart(totals)
			else:
				# Can't consume the entire node, consume partial.
				parts, iaddress = divmod(iaddress, sipart(fragments))
				oaddress += parts * sopart(fragments)
				# enter sub node
				current = sub
				break
		else:
			# not "possible" with full cycle consumption.
			raise RuntimeError("out of bounds")

	# Bottom of the structure
	iparts = sipart(current[2])
	oparts = sopart(current[2])
	for i in range(len(iparts)):
		if iparts[i+1] > iaddress:
			break

	return (cycles, oaddress + oparts[i], iaddress - iparts[i], oparts[i+1] - oparts[i])
