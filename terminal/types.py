"""
# Fundamental classes for representing input from a terminal and caret state management.

# [ Elements ]
# /&Page/
	# &Phrase sequence type.
# /&Text/
	# Alias to the builtin &str.
# /&Words/
	# Tuple identifying total cell count, text, and rendering options.
	# The fundamentals of forming a &Phrase.
"""
from collections.abc import Sequence
import functools
import itertools
import operator
from dataclasses import dataclass
from typing import TypeAlias

from ..system.tty import cells

Text: TypeAlias = str

class Point(tuple):
	"""
	# A pair of integers locating a cell on the screen.
	# Used by &.events.mouse to specify the cursor location.

	# Usually referenced from &.events.Point.
	"""
	__slots__ = ()

	@property
	def x(self):
		return self[0]

	@property
	def y(self):
		return self[1]

	def __add__(self, point, op=int.__add__):
		"""
		# Translate the point relative to another.
		"""
		return self.__class__((op(self[0], point[0]), op(self[1], point[1])))

	def __sub__(self, point, op=int.__sub__):
		"""
		# Subtract the point from another.
		"""
		return self.__class__((op(self[0], point[0]), op(self[1], point[1])))

	@classmethod
	def construct(Class, *points):
		return Class(points)

class Modifiers(int):
	"""
	# Bitmap of modifiers with an imaginary index.

	# The imaginary index is usually not used, but can be used to describe
	# the modifier context or carry additional information about the event.
	"""
	__slots__ = ()

	sequence = (
		'shift',
		'meta',
		'control',
	)
	bits = {
		k: 1 << i for k, i in zip(sequence, range(len(sequence)))
	}

	def __repr__(self):
		return (
			"<" + ('|'.join([
				x for x in self.sequence
				if self.bits[x] & self
			]) or 'none') + ">"
		)

	@property
	def none(self) -> bool:
		"""
		# Whether there are any modifiers present.
		"""
		return not bool(self)

	@property
	def control(self) -> bool:
		return bool(self & 0b100)

	@property
	def meta(self) -> bool:
		return bool(self & 0b010)

	@property
	def shift(self) -> bool:
		return bool(self & 0b001)

	@property
	def imaginary(self, position=len(sequence)):
		"""
		# An arbitrary number designating an imaginary modifier.
		# Defaults to zero.
		"""
		return int(self >> position)

	def test(self, *fields):
		"""
		# Check for the presence of multiple modifiers.

		#!/pl/python
			if mod.test('shift', 'meta'):
				action()
			else:
				no_shift_meta_action()
		"""
		bitset = sum([self.bits[x] for x in fields])
		return bool(bitset & self)

	@classmethod
	@functools.lru_cache(9)
	def construct(Class, bits=0, control=False, meta=False, shift=False, imaginary=0):
		mid = imaginary << 3
		mid |= bits

		if control:
			mid |= Class.bits['control']

		if meta:
			mid |= Class.bits['meta']

		if shift:
			mid |= Class.bits['shift']

		return Class(mid)

class Event(tuple):
	"""
	# An input event from a terminal device.
	"""
	__slots__ = ()

	@property
	def subtype(self) -> str:
		"""
		# The classification of the character with respect to the source.
		"""
		return self[0]
	type=subtype

	@property
	def string(self) -> bytes:
		"""
		# The literal characters, if any, of the event. Used for forwarding key events.
		"""
		return self[1]

	@property
	def identity(self) -> object:
		"""
		# A name for the &string contents; often the appropriate way to process
		# character events. For complex events, this field holds a structure.
		"""
		return self[2]

	@property
	def modifiers(self) -> Modifiers:
		"""
		# The identified &Modifiers of the Character.
		"""
		return self[3]

class Traits(int):
	"""
	# Word attribute bitmap used to describe a part of a &Phrase.

	# The bitmap of attributes allows for conflicting decorations;
	# &..terminal makes no presumptions about how the terminal responds to
	# these, so constraints regarding exclusive settings are not present.
	"""
	__slots__ = ()

	def _build(fields):
		return fields, {
			fields[i]: i for i in range(len(fields))
		}

	fields, field_index = _build(
		(
			# Cell and Text traits.
			'underline',
			'double-underline',

			'inverse',
			'cross',
			'italic',

			'invisible',
			'feint',
			'bold',

			'blink',
			'rapid',

			'overline',
			'frame',
			'encircle',

			'sentinal',
		)
	)
	del _build

	linetypes = (
		'solid',
		'dotted',
		'dashed',
		'curly',
	)

	def __and__(self, rhs):
		return self.__class__(super().__and__(rhs))
	def __or__(self, rhs):
		return self.__class__(super().__or__(rhs))
	def __xor__(self, rhs):
		return self.__class__(super().__xor__(rhs))

	@classmethod
	def all(Class):
		return Class((1 << len(Class.fields)) - 1)

	@classmethod
	def construct(Class, *style, From=0):
		i = From
		for x in style:
			i = i | (1 << Class.field_index[x])

		if not i:
			return Class.none()
		else:
			return Class(i)

	def test(self, *names):
		for trait in names:
			if not self & (1 << self.field_index[trait]):
				return False

		return True

	def __iter__(self):
		for name, i in self.field_index.items():
			if self & (1 << i):
				yield name

	def __str__(self):
		if self:
			return "<" + "|".join(self) + ">"
		return "<notraits>"

	@staticmethod
	def none() -> 'Traits':
		"""
		# Reference to the Zero Traits instance, &NoTraits.
		"""
		return NoTraits

NoTraits = Traits(0)
class RenderParameters(tuple):
	"""
	# Rendering context parameters to use for displaying text on a Terminal.
	# Instances hold the text and cell colors and the &Traits.
	"""
	__slots__ = ()

	_cc_none = -1024
	_tc_none = -1024
	_lc_none = -1024

	@classmethod
	@property
	def default(Class):
		return Class((NoTraits, Class._tc_none, Class._cc_none, Class._lc_none))

	@property
	def traits(self) -> Traits:
		"""
		# The set of &Traits used to style displayed text.
		"""
		return self[0]

	@property
	def textcolor(self) -> int:
		"""
		# The color to use as the text color.
		"""
		return self[1]

	@property
	def cellcolor(self) -> int:
		"""
		# The color to use as the cell's background color.
		"""
		return self[2]

	@property
	def linecolor(self) -> int:
		"""
		# The color to use for the line when the underline trait is present.
		"""
		return self[3]

	@property
	def font(self) -> None:
		"""
		# Configured font.
		# Currently, always &None and ignored by Contexts and Types.
		"""
		return None

	@classmethod
	def from_colors(Class, textcolor:int, cellcolor:int=-1024):
		return Class((NoTraits, textcolor, cellcolor, -1024))

	def set(self, traits:Traits):
		"""
		# Create a new instance with the given &traits added to
		# the traits present in &self.
		"""
		return self.__class__((traits | self[0], *self[1:]))

	def clear(self, traits:Traits):
		"""
		# Create a new instance with the given &traits removed
		# from the traits present in &self.
		"""
		c = self[0]
		return self.__class__((((traits & c) ^ c), *self[1:],))

	def apply(self, *traits, textcolor=None, cellcolor=None, linecolor=None):
		return self.__class__((
			self[0].construct(*traits, From=int(self[0])) if traits else self[0],
			textcolor if textcolor is not None else self[1],
			cellcolor if cellcolor is not None else self[2],
			linecolor if linecolor is not None else self[3],
			*self[4:]
		))

	def update(self, textcolor=None, cellcolor=None, linecolor=None, traits=None):
		return self.__class__((
			traits if traits is not None else self[0],
			textcolor if textcolor is not None else self[1],
			cellcolor if cellcolor is not None else self[2],
			linecolor if linecolor is not None else self[3],
		))

	def form(self, *strings, cells=cells):
		"""
		# Construct words suitable for use by &Phrase associated with the parameters, &self.
		"""
		for text in strings:
			yield Words((cells(text), text, self))

def grapheme(text, index, cells=cells, slice=slice, str=str):
	"""
	# Retrieve the slice to characters that make up an indivisible unit of cells.
	# This is not always consistent with User Perceived Characters.

	# If the given &index refers to a zero width character,
	# find the non-zero width character before the index.
	# If the given &index refers to a non-zero width character,
	# find all the zero width characters after it.

	# ! WARNING:
		# This is **not** consistent with Unicode grapheme clusters.
	"""
	start = text[index:index+1]
	count = 0

	c = cells(str(start))
	if c < 0:
		# check surrogate pair; identify latter part of pair
		# and consume following combinations normally.
		pass

	if c > 0:
		# check after
		for i in range(index+1, len(text)):
			if cells(text[i]):
				break
			count += 1
		return slice(index, index+count+1)
	else: # c==0
		# check before
		for i in range(index-1, -1, -1):
			if cells(text[i]):
				break
			count += 1
		return slice(index-count-1, index+1)

def itergraphemes(text, getslice=grapheme, len=len):
	end = len(text)
	i = 0
	while i < end:
		s = getslice(text, i)
		yield s
		i = s.stop

class Words(tuple):
	"""
	# &Phrase segments identifying the cell count of the word text
	# and the &RenderParameters that should be used to style the text.
	"""
	__slots__ = ()

	@property
	def unit(self) -> int:
		"""
		# The codepoints per character units.
		# Normally `1`. Codepoint length for &Unit and &Redirect.
		"""
		return 1

	@property
	def cellrate(self) -> int:
		"""
		# Number of cells required to display a *character unit* of the word text.
		"""
		return self[0] // (self.unitcount() or 1)

	# Consistent in &Words case, but intend for &text to be adjustable
	# for subclasses like &Redirect.
	text = property(operator.itemgetter(1))

	@property
	def style(self) -> RenderParameters:
		"""
		# The traits and colors to use when rendering the text.
		"""
		return self[2]

	def split(self, whence):
		"""
		# Split the word at the given codepoint offset, &whence.
		"""
		former = self[1][:whence]
		latter = self[1][whence:]
		cr = self.cellrate
		return (
			self.__class__((len(former) * cr, former, self[2])),
			self.__class__((len(latter) * cr, latter, self[2])),
		)

	def cellcount(self) -> int:
		"""
		# Number of cells required to display the word text.

		# This measurement is stored alongside of the string that will be rendered.
		# It is possible, if not likely, that this override be respected above
		# a system's `wcswidth` implementation.
		"""
		return self[0]

	def celloffset(self, offset:int) -> int:
		"""
		# Translate word relative codepoint offset to word relative cell offset.
		"""
		return (offset // (self.unit or 1)) * self.cellrate

	def cellpoint(self, celloffset, *, divmod=divmod):
		"""
		# Translate the word relative &celloffset to the word relative codepoint offset.
		"""
		return divmod(celloffset, self.cellrate)

	def unitcount(self) -> int:
		"""
		# The number of character units in the &codepoints.
		"""
		return self.text.__len__() // (self.unit or 1)

	def unitoffset(self, offset:int) -> int:
		"""
		# Translate word relative codepoint offset to word relative character unit offset.
		"""
		return (offset // (self.unit or 1))

	def unitpoint(self, unitoffset):
		"""
		# Translate word relative Character Unit offset into word relative codepoint offset.
		"""
		uc = self.unitcount()
		if unitoffset < 1:
			return 0, unitoffset
		elif unitoffset < uc:
			return unitoffset, 0
		else:
			return self.text.__len__(), unitoffset - uc

	def codecount(self):
		"""
		# Number of codepoints used to represent the words' text.

		# This is equivalent to `len(Words(...).text)`, but
		# offers a point of abstraction in, very unlikely, implementation changes.
		"""
		return self.text.__len__()

	def codeoffset(self, codeoffset):
		"""
		# The codepoint offset; returns &codeoffset.
		"""
		return codeoffset

	def codepoint(self, codeoffset):
		"""
		# Translate the word relative &codepoint offset to the word relative codepoint offset.
		# A reflective mapping, but bind the returned offset to the word's range returning
		# overflow or underflow as the remainder.
		"""
		txtlen = self.codecount()
		if codeoffset < 0:
			return 0, codeoffset
		elif codeoffset < txtlen:
			return codeoffset, 0
		else:
			return txtlen, codeoffset - txtlen

class Unit(Words):
	"""
	# Words representing a single character unit composed from a
	# unicode codepoint expression. Expressions being regional indicator
	# pairs, emoji ZWJ sequences, and Variant Selector qualified codepoints.

	# Unit words provides the necessary compensation for inconsistent &Words.cellrate.
	"""
	__slots__ = ()

	@property
	def unit(self) -> int:
		return self.text.__len__()

	def split(self, offset):
		"""
		# Maintain &Words.split interface, but always return a tuple with a sole element.
		"""
		if offset < self.codecount():
			return (Unit((0, "", self.style)), self)
		else:
			return (self, Unit((0, "", self.style)))

class Redirect(Unit):
	"""
	# A &Unit that explicitly remaps its display text.
	# Used to control the transmitted representations of control characters and indentation.
	"""

	text = property(operator.itemgetter(3))

class Phrase(tuple):
	"""
	# A sequence &Words providing translation interfaces for codepoints, cells, and character
	# units.
	"""
	__slots__ = ()

	@staticmethod
	def frame_word(rp, cells, text):
		"""
		# Select the appropriate &Words class for containing the &text.
		# Order of parameters is intended to support &from_segmentation.
		"""
		if cells < 0:
			# Negative cell counts are the indicator used by &..system.words
			# to isolate Character Units. It's applied here using &Unit.
			return Unit((-cells, text, rp))
		else:
			return Words((cells, text, rp))

	@classmethod
	def segment(Class, qwords, *,
			starmap=itertools.starmap,
			chain=itertools.chain,
			partial=functools.partial,
		):
		return chain.from_iterable(
			# Partial the RenderParameters to frame_word in order to
			# distribute the styles to all the words.
			starmap(partial(Class.frame_word, rp), wordi)
			for rp, wordi in qwords
		)

	m_unit = (
		Words.unitcount,
		Words.unitoffset,
		Words.unitpoint,
	)
	m_cell = (
		Words.cellcount,
		Words.celloffset,
		Words.cellpoint,
	)
	m_codepoint = (
		Words.codecount,
		Words.codeoffset,
		Words.codepoint,
	)

	@property
	def text(self) -> str:
		"""
		# The text content of the phrase.
		"""
		return ''.join(w.text for w in self)

	@staticmethod
	def default(text, traits=RenderParameters((Traits(0), None, None, None))):
		"""
		# Construct a Word Specification with default text attributes.
		"""
		return (text, traits)

	@classmethod
	def wordspace(Class):
		"""
		# Word specification consisting of a single space.
		"""
		return Class.default(" ")

	@classmethod
	def from_words(Class, *words:Words, ichain=itertools.chain.from_iterable):
		return Class(ichain(words))

	@classmethod
	def from_segmentation(Class, qwords):
		return Class(Class.segment(qwords))

	def join(self, phrases, zip=zip, repeat=itertools.repeat, ichain=itertools.chain.from_iterable):
		"""
		# Create a new Phrase from &phrases by placing &self between each &Phrase instance
		# in &phrases.
		"""
		if not phrases:
			return self.__class__(())

		i = ichain(ichain(zip(repeat(self, len(phrases)), phrases)))
		next(i)
		return self.__class__((i))

	@classmethod
	def construct(Class,
			specifications:Sequence[object],
			RenderParametersConstructor=RenderParameters,
			cells=cells, str=str
		):
		"""
		# Create a &Phrase instance from the &specifications designating
		# the text of the words and their properties.

		# [ Parameters ]
		# /specifications/
			# The words and their attributes making up the phrase.
		"""
		specs = [
			Words((cells(str(spec[0])), spec[0], RenderParameters(spec[1:])))
			for spec in specifications
		]

		return super().__new__(Class, specs)

	def combine(self):
		"""
		# Combine word specifications with identical attributes(styles).
		# Returns a new &Phrase instance with any redundant word attributes eliminated.
		"""

		out = [self[0]]
		cur = out[-1]

		for spec in self[1:]:
			if spec[2] == cur[2]:
				cur = out[-1] = (cur[0] + spec[0], cur[1] + spec[1], cur[3:])
			else:
				out.append(spec)
				cur = spec

		return self.__class__(out)

	def cellcount(self):
		"""
		# Number of cells that the phrase will occupy.
		"""
		return sum(x[0] for x in self)

	def unitcount(self):
		"""
		# Number of character units contained by the phrase.
		"""
		return sum(x.unitcount() for x in self)

	def translate(self, *indexes, iter=iter, len=len, next=next, cells=cells):
		"""
		# Get the cell offsets of the given character indexes.

		# [ Parameters ]
		# /indexes/
			# Ordered sequence of grapheme (cluster) indexes to resolve.
			# (Currently a lie, it is mere character index translation)
		"""
		offset = 0
		nc = 0
		noffset = 0

		if not self:
			for x in indexes:
				if x == 0:
					yield 0
				else:
					raise IndexError(indexes[0])
			return

		i = iter(y[:2] for y in self)
		x = next(i)

		c, t = x
		chars = len(t)
		noffset = offset + chars

		for y in indexes:
			while x is not None:
				if noffset >= y:
					# found index, report and jump to next index
					yield nc + cells(t[:y-offset])
					break

				nc += c
				offset = noffset
				try:
					x = next(i)
				except StopIteration:
					yield None
					break

				# New words.
				c, t = x
				chars = len(t)
				noffset = offset + chars
			else:
				# index out of range
				yield None

	def findcells(self, *offsets, index=(0,0,0)):
		lfc = self.lfindcell
		last = 0
		for co in offsets:
			index = lfc(co - last, index)
			last = co
			yield index

	def reverse(self):
		"""
		# Construct an iterator to the concrete words for creating a new &Phrase
		# instance that is in reversed form of the words in &self.
		# `assert phrase == Phrase(Phrase(phrase.reverse()).reverse())`
		"""
		return (
			(x[0], x[1].__class__(reversed(x[1])),) + x[2:]
			for x in reversed(self)
		)

	def subphrase(self, start, stop, adjust=(lambda x: x)):
		"""
		# Extract the subphrase at the given cell offsets.
		"""

		return self.__class__(self.select(start, stop, adjust))

	def select(self, start, stop, adjust=(lambda x: x), cells=cells):
		"""
		# Extract the subphrase at the given indexes.

		# [ Parameters ]
		# /adjust/
			# Callable that changes the text properties of the selected words.
			# Defaults to no change.
		"""
		start_i, char_i, acell_i = start
		stop_i, schar_i, bcell_i = stop

		if start_i == stop_i:
			# Single word phrase.
			word = self[start_i]
			text = word[1][char_i:schar_i]
			yield (cells(text), text, adjust(word[2]))
		else:
			word = self[start_i]
			text = word[1][char_i:]
			if text:
				yield (cells(text), text, adjust(word[2]))

			yield from self[start_i+1:stop_i]

			word = self[stop_i]
			text = word[1][:schar_i]
			if text:
				yield (cells(text), text, adjust(word[2]))

	# lfindcell and rfindcell are conceptually identical,
	# but it's a little tricky to keep the Python implementation dry
	# without introducing some unwanted overhead.
	# So, the implementation redundancy is permitted with the minor variations.

	def lfindcell(self,
			celloffset:int, start=(0,0,0),
			map=map, len=len, range=range,
			cells=cells, islice=itertools.islice
		):
		"""
		# Find the word and character index using a cell offset.
		"""

		wordoffset, character_index, wordcell = start
		# relative to wordcell for continuation support
		offset = celloffset + wordcell
		cell_index = wordcell

		i = l = 0
		if wordoffset < 16:
			# Small offset? recalc from sum.
			s = sum(x[0] for x in self[:wordoffset])
		elif character_index:
			# Large offset, recalc from cells.
			s = wordcell - cells(self[wordoffset][1][:character_index])
		else:
			s = wordcell

		nwords = len(self)
		ri = range(wordoffset, nwords, 1)

		# Scan for offset wrt the cells.
		for i in ri:
			l = self[i][0]
			s += l
			if s >= offset:
				if i != wordoffset:
					# Reset index if in a new word.
					character_index = 0
				break
			cell_index = s
		else:
			# celloffset is beyond the end of the phrase
			return None

		itext = self[i][1]

		charcells = 0
		for charcells in map(cells, islice(itext, character_index, None)):
			if cell_index >= offset:
				break
			cell_index += charcells
			character_index += 1

		# Greedily skip any adjacent zerowidth characters.
		# rfindcell does this naturally.
		for charcells in map(cells, islice(itext, character_index, None)):
			if charcells:
				# Not zero width, keep current index.
				break
			character_index += 1
		else:
			# End of word; empty string.
			while not self[i][1][character_index:character_index+1]:
				i += 1
				if i == nwords:
					i -= 1
					break
				character_index = 0

		return (i, character_index, cell_index)

	def rfindcell(self,
			celloffset:int, start=(-1,0,0),
			map=map, len=len, range=range,
			cells=cells, islice=itertools.islice
		):
		"""
		# Find the word and character index using a cell offset.
		"""

		wordoffset, character_index, wordcell = start

		# relative to wordcell for continuation support
		offset = celloffset + wordcell
		cell_index = wordcell

		i = l = 0
		nwords = len(self)
		ri = range(wordoffset, -nwords-1, -1)

		if wordoffset > -16:
			s = sum(x[0] for x in self[nwords+wordoffset+1:])
		elif character_index:
			s = wordcell - cells(self[wordoffset][1][-character_index:])
		else:
			s = wordcell

		for i in ri:
			l = self[i][0]
			s += l
			if s >= offset:
				if i != wordoffset:
					character_index = 0
				break
			cell_index = s
		else:
			# celloffset is beyond the beginning of the phrase.
			return None

		itext = self[i][1]
		istart = len(itext)-character_index-1

		for charcells in map(cells, (itext[x] for x in range(istart, -1, -1))):
			if cell_index >= offset:
				break
			cell_index += charcells
			character_index += 1
		else:
			# End of word
			if nwords + i == 0:
				# End of Phrase.
				pass
			elif cell_index == offset:
				# Only step into the next word if it's not torn.
				i -= 1
				character_index = 0

		return (i, character_index, cell_index)

	def lstripcells(self,
			cellcount:int, substitute=(lambda x: '*'),
			list=list, len=len, range=range,
			cells=cells
		):
		"""
		# Remove the given number of cells from the start of the phrase.

		# If the cell count traverses a wide character, the &substitute parameter is
		# called with the character as its only argument and the result is prefixed
		# to the start of the phrase.
		"""

		if cellcount <= 0:
			# Zero offset, no trim.
			return self

		i, character_index, cell_index = self.lfindcell(cellcount)
		itext = self[i][1]

		if cellcount == cell_index:
			# Aligned.
			txt = itext[character_index:]
		else:
			# Cut on wide character and substitute.
			g = grapheme(itext, character_index - 1)
			txt = substitute(itext[g]) + itext[character_index:]

		# final words
		out = list(self[i:]) # Include the i'th; it will be overwritten.
		out[0] = ((cells(txt), txt,) + out[0][2:])

		return self.__class__(out)

	def rstripcells(self,
			cellcount:int, substitute=(lambda x: '*'),
			list=list, len=len, range=range,
			cells=cells
		):
		"""
		# Remove the given number of cells from the end of the phrase.

		# If the cell count traverses a wide character, the &substitute parameter is
		# called with the character as its only argument and the result is suffixed
		# to the end of the phrase.
		"""

		if cellcount <= 0:
			# Zero offset, no trim.
			return self

		i, rcharacter_index, cell_index = self.rfindcell(cellcount)

		out = list(self[:len(self)+i+1])
		itext = out[-1][1]
		character_right_offset = len(itext) - rcharacter_index

		if cellcount == cell_index:
			# Aligned on character.
			txt = itext[:character_right_offset]
		else:
			# Tear multicell character and substitute.
			g = grapheme(itext, character_right_offset)
			txt = itext[:g.start] + substitute(itext[g])

		# final words
		out[-1] = ((cells(txt), txt,) + out[-1][2:])

		return self.__class__(out)

	def seek(self, whence, offset:int,
			ulength=(lambda w: len(w.text)),
			uoffset=(lambda w, i: i),
			utranslate=(lambda w, i: (i, 0)),
			*,
			map=map, len=len, range=range, abs=abs,
		):
		"""
		# Find the word offset and codepoint offset for the unit &offset
		# relative to &whence.
		# The &offset is traversed using &ulength, &uoffset, and &uindex.
		"""

		if offset == 0 or not self:
			return whence, offset

		wordi, chari = whence
		fword = self[wordi]
		ui = uoffset(fword, chari)

		# Scan words forwards (+) or backwards (-) based on &offset.
		# Maintain invariant here by adjusting &re to be relative
		# to beginning or end of the word. Enables the following loop
		# to always subtract the length of the word.
		if offset < 0:
			re = -offset
			ri = range(wordi, -1, -1)
			re += uoffset(fword, len(fword.text)) - ui
			lswitch = -1
		else:
			re = offset
			ri = range(wordi, len(self), 1)
			re += ui - uoffset(fword, 0)
			lswitch = 0

		# Scan for word with offset.
		for i in ri:
			word = self[i]
			ll = ulength(word)
			if re <= ll:
				# Boundary crossed within or at the edge of &word.
				break
			re -= ll
		else:
			assert re > 0
			# Offset exceeded bounds.
			# Report beginning or end and remaining offset.
			if offset < 0:
				return (0, 0), re
			else:
				return (len(self)-1, len(self[-1][1])), re

		ci, r = utranslate(word, abs(re + (lswitch * ll)))
		return (i, ci), -r

	def afirst(self, position):
		"""
		# Align the position to the beginning of the next word given
		# that the character index is at the end of the word
		# and that there is a following word. If realignment is not
		# possible, return &position.
		"""
		wi, ci = position

		if wi >= (len(self) - 1):
			return position

		if ci < len(self[wi].text):
			return position

		return (wi+1, 0)

	def alast(self, position):
		"""
		# Align the position to the end of the previous word given
		# that the character index is at the start of the word
		# and that there is a previous word. If realignment is not
		# possible, return &position.
		"""
		wi, ci = position
		if wi < 1 or ci > 0:
			return position
		else:
			return (wi-1, len(self[wi-1].text))

	def split(self, whence, *, chain=itertools.chain):
		"""
		# Split the phrase at the given position, &whence.
		"""
		wordi, codei = whence
		Class = self.__class__
		if not self:
			yield Class(())
			yield Class(())
			return
		w = self[wordi]
		pair = w.split(codei)
		yield Class(chain(self[0:wordi], pair[:1]))
		yield Class(chain(pair[1:], self[wordi+1:]))

	def tell(self, position,
			ulength=(lambda w: len(w.text)),
			uoffset=(lambda w, i: i),
			utranslate=(lambda w, i: (i, 0)), *,
			sum=sum, range=range
		):
		"""
		# Identify the absolute unit offset for the given phrase position.

		# [ Parameters ]
		# /position/
			# The Word-Codepoint offset pair being described.
		"""
		if not self:
			return 0
		wi, ci = position
		offset = uoffset(self[wi], ci)
		return offset + sum(ulength(self[i]) for i in range(wi))

# Common descriptor endpoint.
Page: TypeAlias = Sequence[Phrase]
