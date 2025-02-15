"""
# Line and character format interpretation and serialization.
"""
from collections.abc import Sequence, Iterable
from typing import Callable, TypeAlias

from ..context.tools import partial
from ..context.tools import struct

@struct()
class Fields(object):
	"""
	# Format configuration for separating the fields in a line of syntax.

	# Essentially, a structured &partial instance that provides an interface
	# consistent with other &.format data structures. &separation intends
	# to be used to identify the configuration that &isolate uses in order
	# separate the fields of a string. In many cases, &separation should be
	# the instance of a class and &isolate should be an unbound method that
	# performs the desired functionality.

	# [ Elements ]
	# /separation/
		# The primary context or means for performing field isolation.
		# Often, a pattern or configuration.
	# /isolate/
		# The field producing function that is given &separation as
		# its first argument and line content as the second.
	"""

	separation: object
	isolate: Callable[[object, str], Iterable[tuple[str,str]]]

	def partial(self, *argv, **kw):
		"""
		# Construct a direct call to &isolate with &separation
		# and the given arguments bound to the call.
		"""

		return partial(self.isolate, self.separation, *argv, **kw)

	def structure(self, lines:Iterable[object]) -> Iterable[Sequence[tuple[str,str]]]:
		"""
		# Perform &isolate against the given &lines.
		"""

		return map(list, map(self.partial(), lines))

	def sequence(self, fields:Iterable[tuple[str,str]], *, index=-1) -> Iterable[str]:
		"""
		# Reconstruct the original lines from the given field vectors.
		"""

		for fv in fields:
			yield ''.join(x[index] for x in fv)

@struct()
class Lines(object):
	"""
	# Format configuration for reading and writing indented syntax lines.
	"""

	termination: str = '\n'
	indentation: str = '\t'

	@staticmethod
	def _splitpartial(lt, text, leading='', *, limit=-1) -> tuple[str, Sequence[str]]:
		"""
		# Interpret the given &text as a sequence of lines using the
		# configured &termination character.

		# The &leading string is prefixed to the first line in the split,
		# and the final line is removed and returned as the remainder to
		# be passed back in as &leading to the next call.

		# Use &split when &text is known to be complete.

		# [ Returns ]
		# A pair of values. The remainder from the split and the
		# split lines with the given &leading prefixed on the first line.
		"""

		# Normal split. Toss line ends.
		lines = (leading + text).split(lt, maxsplit=limit)

		# Prefix first line with leading, expected to be the remainder
		# of the last call when processing larger volumes of text.
		remainder = lines[-1]
		del lines[-1:]

		return remainder, lines

	def measure_partial_termination(self, line:str) -> int:
		"""
		# Identify the number of characters at the end of the &line that
		# intersect with &termination.
		"""

		for i in range(len(self.termination) - 1, 0, -1):
			if line[-i:] == self.termination[:i]:
				return i
		return 0

	def measure_indentation(self, line:str) -> int:
		"""
		# Identify the indentation level of the given &line by counting the
		# leading &indentation characters.
		"""

		i = 0
		ic = self.indentation
		isz = len(ic)

		for co in range(0, len(line), isz):
			if line[co:co+isz] != ic:
				return i
			i += 1

		# All charactere were &ic.
		return len(line)

	def level(self, line:str) -> tuple[int, str]:
		"""
		# Measure the indentation of &line and reconstruct it as a tuple
		# expressing the indentation level as an integer and the content
		# of the line without the indentation characters.
		"""

		ilsz = len(self.indentation)
		il = self.measure_indentation(line)
		return (il, line[il*ilsz:])

	def structure(self, itext:Iterable[str]) -> Iterable[tuple[int, str]]:
		"""
		# Structure the given iterator of strings as an iterator of lines.

		# Excludes a final empty line.
		"""

		# Special case this here in order to allow structuring without
		# indentation detection. However, if direct use of &level is
		# performed, &measure_indentation will raise an exception for a zero step size.
		if len(self.indentation) == 0:
			level = (lambda l: (0, l))
		else:
			level = self.level

		it = iter(itext)
		leading = ''
		remainder = ''
		splitp = self._splitpartial

		# Again, but lines have been seen.
		for textbuf in it:
			remainder, lines = splitp(self.termination, textbuf, leading)
			yield from map(level, lines)
			leading = remainder

		if remainder:
			yield level(remainder)

	def sequence(self, ilines:Iterable[tuple[int, str]]) -> Iterable[str]:
		"""
		# Reconstruct the original lines from an iterable of indentation level
		# and line content pairs.

		# Includes a final empty line.
		"""

		for il, lc in ilines:
			yield (il * self.indentation) + lc + self.termination

@struct()
class Characters(object):
	"""
	# Character encoding and decoding configuration.

	# Primarily, a minor abstraction for Python's codecs providing
	# &structure and &sequence interfaces that can be composed with &Lines.

	# [ Elements ]
	# /encoding/
		# Name of encoding whose encoding and decoding functions are assigned
		# to the instance.
	# /Encoder/
		# Constructor for incremental encoding.
	# /Decoder/
		# Constructor for incremental decoding.
	# /encode/
		# Direct access to complete sole string encoding function.

		# Performance is inferior to &str.encode when invoking many times.
	# /decode/
		# Direct access to complete sole bytes decoding function.

		# Performance is inferior to &bytes.decode when invoking many times.
	"""

	encoding: str
	Encoder: Callable[[], tuple[Callable[[str], bytes], Callable[[], bytes]]]
	Decoder: Callable[[], tuple[Callable[[str], str], Callable[[], str]]]
	encode: Callable[[str], bytes]
	decode: Callable[[bytes], str]

	@staticmethod
	def _alloc_coder_pair(coder, method, final):
		# Constructor for allocating encoding/decoding state.
		transform = getattr(coder(), method)
		return (transform, partial(transform, final, final=True))

	@staticmethod
	def _alloc_codec_constructors(ci, errors):
		# Constructor for getting the incremental classes.
		return (
			partial(ci.incrementalencoder, errors),
			partial(ci.incrementaldecoder, errors),
		)

	@classmethod
	def from_codec(Class, encoding:str, errors:str):
		"""
		# Create an instance using a Python &encoding and &errors handling scheme.

		# If mixed error handling is needed in one instance, create two instances
		# with &from_codec and combine the fields as needed into a third
		# instance.
		"""

		from codecs import lookup # Late import to defer dependency until use.
		ci = lookup(encoding)
		cie, cid = Class._alloc_codec_constructors(ci, errors)

		# Bound for the lambdas given to &Class.
		encode = ci.encode
		decode = ci.decode

		return Class(
			encoding,
			partial(Class._alloc_coder_pair, cie, 'encode', str()),
			partial(Class._alloc_coder_pair, cid, 'decode', bytes()),
			(lambda x: encode(x, errors)[0]),
			(lambda x: decode(x, errors)[0]),
		)

	def sequence(self, itext:Iterable[str]) -> Iterable[bytes]:
		"""
		# Encode the strings produced by &itext as &bytes.
		"""

		encode_txt, finish = self.Encoder()
		for txt in itext:
			yield encode_txt(txt)

		yield finish()

	def structure(self, ibytes:Iterable[bytes]) -> Iterable[str]:
		"""
		# Decode the data produced by &ibytes as unicode strings.
		"""

		decode_txt, finish = self.Decoder()
		for segment in ibytes:
			yield decode_txt(segment)

		yield finish()
