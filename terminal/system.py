"""
# System defined or dependent functions.

# [ Elements ]
# /cells/
	# &..terminal access point for a `wcswidth` interface
	# capable of handling control characters, ZWJ, ZWNJ, Regional Indicators,
	# and Variation Selectors.
"""
from collections.abc import Iterable
from ..system.tty import cells

def graphemes(ci:Iterable[str], ctlen=0, tablen=8):
	"""
	# Recognize Character Units from an iterator of codepoints using &cells.

	# Identification of Character Units is performed by analyzing the cell usage of
	# contiguous codepoints. When a change in cell usage occurs, presume that
	# a new Character Unit has begun. However, do so while considering
	# Variant Selector, ZWJ Sequence, and Regional Indicator exceptions.

	# ! WARNING:
		# ZWJ sequences are nearly presumed to be emoji sequences;
		# the maximum cell count of the codepoints in the sequence determines
		# the reported cells. While this may yield the correct alignment
		# outside of emoji, there are cases where a join intends to represent
		# two character units in which the identified maximum will be incorrect.

	# [ Parameters ]
	# /ci/
		# Iterable of unicode characters.
	# /ctlen/
		# Cell count to assign to low-ascii control characters.
	# /tablen/
		# Cell count to assign to tab characters.

	# [ Regional Indicators ]
	# Currently uses range checks. If (python/keyword)`match` ever implements
	# jump tables for constants, the following template can be used to generate
	# the or-list.

	#!syntax/python
		ri_offset = 0x1F1E6
		ri_codes = [
			(hex((x - ord('a')) + ri_offset))[2:].upper()
			for x in range(ord('a'), ord('z'))
		]
		for p in ri_codes[0::4], ri_codes[1::4], ri_codes[2::4], ri_codes[3::4]:
			print('"' + '" | "\\U000'.join(p) + '" | \\')
	"""

	ci = iter(ci)
	unit = ""
	unitlen = 0
	ext = ""
	extlen = 0
	cp = ""

	for cp in ci:
		if cp > '\u2000':
			if cp < '\uFE00':
				if cp == '\u200D':
					# ZWJ Sequence continuation.
					try:
						unit += cp + next(ci)
					except StopIteration:
						# Final codepoint in iterator.
						unit += cp
						break
					continue
				elif cp == '\u200C':
					# ZWNJ Word Isolation.
					if unit:
						yield (unitlen, unit)
						unit = ""
						unitlen = 0
					yield ('\u200C', 0)
					continue
			else:
				# >= \uFE00
				if cp <= '\uFE0F':
					# VS modification.
					# Qualifies the former codepoint.
					# Always overwrites previous unitlen.
					unit += cp
					unitlen = cells(unit, ctlen, tablen)
					continue
				elif cp >= '\U0001F1E6' and cp <= '\U0001F1FF':
					# Handle Variation Selector, ZWNJ and ZWJ specially.
					# If paired, overwrite and continue.
					if unit and unit[-1:] >= '\U0001F1E6' and unit[-1:] <= '\U0001F1FF':
						former = unit[-2:-1]
						if former and former >= '\U0001F1E6' and former <= '\U0001F1FF':
							# Three consecutive RIs, break unit.
							yield (unitlen, unit)
							unit = cp
							unitlen = cells(cp, ctlen, tablen)
							continue
						else:
							# Two consecutive RIs.
							unit += cp
							unitlen = cells(unit, ctlen, tablen)
							continue
		else:
			# Avoid optimizing here as probing the system's
			# configuration may be desireable. For the normal case
			# of one cell per codepoint, the selection of a fast
			# path is the responsibility of the caller.
			pass

		# Detect units by whether or not they increase the cell usage.
		# Zero-length additions are continued until terminated by
		# a change in the cell count.
		ext = unit + cp
		extlen = cells(ext, ctlen, tablen)

		if unit and extlen > unitlen:
			# Completed.
			yield (unitlen, unit)
			unit = cp
			unitlen = cells(cp, ctlen, tablen)
		else:
			# Continued.
			unit = ext
			unitlen = extlen

	# Emit remainder if non-zero.
	if unit:
		yield (unitlen, unit)

def words(gi:Iterable[tuple[str, int]]) -> tuple[int, str]:
	"""
	# Group Character Units by the cell usage rate. Exceptions given to already plural
	# strings which expect to be treated as units.

	# Processes the &graphemes generator into cell counts and string pairs providing
	# the critical parameters for &.types.Words and &.types.Unit instances.

	# [ Parameters ]
	# /gi/
		# Iterator producing codepoint expression and cell count pairs.

	# [ Returns ]
	# Iterator of cells and strings where negative cell counts indicate a
	# a sole Character Unit.

	# The integer and string positions are swapped in order to be consistent
	# with &.types.Words order.
	"""
	current = 0
	chars = []
	for cc, u in gi:
		unit = len(u) > 1
		if cc != current or unit:
			if chars:
				yield (current * len(chars)), ''.join(chars)
				del chars[:]

			if unit or ord(u) < 32:
				yield -cc, u
				cc = 0
			else:
				chars.append(u)
			current = cc
		else:
			# Continue group.
			chars.append(u)

	if chars:
		yield (current * len(chars)), ''.join(chars)
