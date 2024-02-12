"""
# Relative path resolution.
"""
from collections.abc import Sequence

def relative(points:Sequence[str], delta=({'':0, '.':0, '..':1}).get) -> Sequence[str]:
	"""
	# Resolve relative accessors within &points.
	"""
	r:list[str] = []
	add = r.append
	change = 0

	for x in points:
		a = delta(x)
		if a is not None:
			change += a
		else:
			if change:
				# Apply ascent.
				del r[-change:]
				change = 0
			add(x)
	else:
		if change:
			del r[-change:]

	return r
