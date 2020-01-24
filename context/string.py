"""
# Supplemental string operations.
"""
import itertools
import operator

def ilevel(string:str, indentation='\t', take=itertools.takewhile, sum=sum) -> int:
	"""
	# Return the indentation level of the given string.
	"""
	return sum(1 for i in take(indentation.__eq__, string))

def indent(string:str, level:int=1, indentwith:str='\t') -> str:
	"""
	# Indent the given &string using the &level * &indentwith.
	"""

	lines = string.splitlines(True)
	i = (level * indentwith)

	return (i if lines else i.__class__()) + i.join(lines)

def normal(string:str, separator:str=' ') -> str:
	"""
	# Normalize the whitespace in the given string.
	"""

	return separator.join((x for x in string.split() if not x.isspace()))

def slug(string:str, separators=str.maketrans('_', ' '), replacement:str='-') -> str:
	"""
	# Convert &separators and spaces into single &replacement instances inside &string.
	"""
	return normal(string.translate(separators), replacement)

def varsplit(indicator, string):
	"""
	# str.split() translating series of tokens into numbers instead
	# of mere separations. The returned list has the pattern: `[str, int, str, int, ...]`.
	"""
	parts = iter(string.split(indicator))

	yield next(parts)

	count = 1
	for x in parts:
		if x:
			yield count
			yield x
			count = 1
		else:
			count += 1
	else:
		# substract the implicit increment on the tail.
		count -= 1

	# trailing indicators
	if count:
		yield count
		yield ""
