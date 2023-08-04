"""
# Character matrix rendering contexts.

# Holds &Type, &Context and &Screen defintions for constructing escape sequences
# to be transmitted to the terminal.

# [ Engineering ]
# Many sequence codes are hardcoded in &Context and &Screen. The exact codes
# should be moved to &Type and symbolically referenced in preparation for some termcap
# loading.
"""
from collections.abc import Iterable, Sequence
import functools
import itertools
import codecs

from . import types

class Type(object):
	"""
	# Terminal Type data structure and cache for composing instruction sequences.

	# Conceptually, this is a Terminal Capabilities set coupled with an encoding. However,
	# standard terminfo databases are not referenced as the target applications are those
	# committed to modern terminal emulators supporting commonly employed standards or practices.

	# [ Engineering ]
	# Currently unstable API. It was quickly ripped out of &Context.
	"""

	normal_render_parameters = types.RenderParameters((types.NoTraits, -1024, -1024, -1024))

	_escape_character = b'\x1b'
	_field_separator = b';'
	_join = _field_separator.join
	_csi_init = _escape_character + b'['
	_osc_init = _escape_character + b']'
	_st = _escape_character + b'\\' # String Terminator
	_wm = b't'
	_ul_color = (b'58', b'59')

	# Private Modes
	_pm_set = b'h'
	_pm_reset = b'l'
	_pm_save = b's'
	_pm_restore = b'r'
	_pm_init = _csi_init + b'?'

	# Synchronize with &.control
	_pm_origin = 6
	_pm_screen = 1049

	_reset_text_attributes = b'0'

	# Support for SGR color.
	@staticmethod
	def select_foreground_16(code, offsets=(30, 90)):
		return offsets[code//8] + (code % 8)

	@staticmethod
	def select_background_16(code, offsets=(40, 100)):
		return offsets[code//8] + (code % 8)

	select_foreground_256 = b'38;5'
	select_background_256 = b'48;5'
	select_underline_256 = b'58;5'
	select_foreground_rgb = b'38;2'
	select_background_rgb = b'48;2'
	select_underline_rgb = b'58;2'

	# Pairs are of the form: (Initiate, Terminate)
	style_codes = {
		'bold': (b'1', b'22'),
		'feint': (b'2', b'22'),
		'blink': (b'5', b'25'),
		'rapid': (b'6', b'25'),

		'italic': (b'3', b'23'),
		'underline': (b'4', b'24'),
		'inverse': (b'7', b'27'),
		'invisible': (b'8', b'28'),
		'cross': (b'9', b'29'),

		# Does not appear to be commonly supported.
		'double-underline': (b'21', b'24'),
		'frame': (b'51', b'54'),
		'encircle': (b'52', b'54'),
		'overline': (b'53', b'55'),
	}

	def esc(self, string:bytes):
		"""
		# Escape prefixed string.

		# [ Parameters ]
		# /string/
			# The bytes that will be prefixed with the configured escape.
		"""
		return self._escape_character + string

	def csi(self, terminator:bytes, *parts:bytes):
		"""
		# Control Sequence Introducer constructor.

		# [ Parameters ]
		# /terminator/
			# The end of the CSI; intermediates and termination character.
		# /parts/
			# The decimal parameter codes as ASCII encoded byte strings.
		"""
		return self._csi_init + self._join(parts) + terminator

	def osc(self, *parts):
		"""
		# Operating System Command.
		"""
		return self._osc_init + self._join(parts) + self._st

	def csi_filter_empty(self, terminator:bytes, *parts:bytes):
		"""
		# &csi variant that returns an empty string when &parts is empty.
		"""
		if parts == ():
			return b''
		return self._csi_init + self._join(parts) + terminator

	def wm(self, *parts:int):
		"""
		# Window Manipulations.
		"""
		return self._csi_init + self._join(map(self.cached_integer_encode, parts)) + self._wm

	def pm(self, terminator:bytes, parts:bytes):
		"""
		# Private Mode Values. (DECSET/DECRST)
		"""
		return self._pm_init + self._join(parts) + terminator

	def decset(self, options):
		"""
		# Set Private Mode values.
		"""
		return self.pm(self._pm_set, map(self.cached_integer_encode, options))

	def decrst(self, options):
		"""
		# Reset Private Mode values.
		"""
		return self.pm(self._pm_reset, map(self.cached_integer_encode, options))

	def pm_save(self, options):
		"""
		# Save Private Mode values.
		"""
		return self.pm(self._pm_save, map(self.cached_integer_encode, options))

	def pm_restore(self, options):
		"""
		# Restore Private Mode values.
		"""
		return self.pm(self._pm_restore, map(self.cached_integer_encode, options))

	def wm_title(self, title):
		"""
		# Instruct the emulator to use the given title for the window.
		# The given &title should be plain text and control characters will be translated.
		"""
		etitle = self.encode(title)
		return self._osc_init + b"2;" + etitle + b"\x07"

	def replicate(self, vfrom, vto, vtarget, *, page=(1, 1)):
		"""
		# Copy the rectangle identified by &vfrom and &vto to the position identified
		# by &vtarget.
		"""
		return self.csi(b'v',
			self.cached_integer_encode(vfrom[1]),
			self.cached_integer_encode(vfrom[0]),
			self.cached_integer_encode(vto[1]),
			self.cached_integer_encode(vto[0]),
			self.cached_integer_encode(page[0]),
			self.cached_integer_encode(vtarget[1]),
			self.cached_integer_encode(vtarget[0]),
			self.cached_integer_encode(page[1]) + b'$',
		)

	def erase(self, vfrom, vto):
		"""
		# Erase the rectangle identified by &area.
		"""
		return self.csi(b'z',
			self.cached_integer_encode(vfrom[1]),
			self.cached_integer_encode(vfrom[0]),
			self.cached_integer_encode(vto[1]),
			self.cached_integer_encode(vto[0]) + b'$',
		)

	def insert_characters(self, count):
		"""
		# ICH, make room for &count characters. Maintains characters after the insertion.
		"""
		return self.csi(b'@', self.cached_integer_encode(count))

	def delete_characters(self, count):
		"""
		# DCH, delete character moving remaining characters left.
		"""
		return self.csi(b'P', self.cached_integer_encode(count))

	def insert_lines(self, count):
		"""
		# IL, make room for &count lines. Maintains lines after the insertion.
		"""
		return self.csi(b'L', self.cached_integer_encode(count))

	def delete_lines(self, count):
		"""
		# DL, remove &count lines. Moves lines following the deleted up.
		"""
		return self.csi(b'M', self.cached_integer_encode(count))

	def scroll_up(self, count):
		"""
		# SU, adjust the scrolling region's view by scrolling up &count lines.
		"""
		return self.csi(b'S', self.cached_integer_encode(count))

	def scroll_down(self, count):
		"""
		# SD, adjust the scrolling region's view by scrolling down &count lines.
		"""
		return self.csi(b'T', self.cached_integer_encode(count))

	def select_color(self, target, color_code, /,
			targets_rgb={
				'text':select_foreground_rgb,
				'cell':select_background_rgb,
				'line':select_underline_rgb,
			},
			targets_256={
				'text':select_foreground_256,
				'cell':select_background_256,
				'line':select_underline_256,
			},
			targets_reset={'text': 39, 'cell': 49, 'line': 59},
			str=str, map=map
		):
		"""
		# Values beyond 24-bit are ignored.
		# Negatives select from traditional palettes or stored references.
		"""
		cie = self.cached_integer_encode

		if color_code >= 0:
			r = (color_code >> 16) & 0xFF
			g = (color_code >> 8) & 0xFF
			b = (color_code >> 0) & 0xFF

			return (targets_rgb[target], self._join(map(cie, (r, g, b))))
		else:
			color_code = -color_code

			if color_code <= 256:
				# 1-256 inclusive; 0 (-0) is recognized as a 24-bit color.
				return (targets_256[target], cie(color_code-1))
			elif color_code == 1024:
				# Special code for defaults.
				return (cie(targets_reset[target]),)
			else:
				# Sixteen colors offset at 512.
				color_code -= 512
				assert color_code < 16

				if target == 'text':
					return (cie(self.select_foreground_16(color_code)),)
				elif target == 'cell':
					return (cie(self.select_background_16(color_code)),)
				else:
					raise ValueError("tty-16 colors not available for target: " + target)

	@staticmethod
	def transition_traits(style_codes, from_traits, to_traits, chain=itertools.chain):
		kept = from_traits & to_traits # traits to ignore

		# Must precede newtraits.
		cleartraits = kept ^ from_traits
		tclear = (style_codes[x][1] for x in cleartraits)

		# Must follow cleartraits as some trait exits apply to multiple
		# enters. (double-underline and underline for instance)
		newtraits = kept ^ to_traits
		tset = (style_codes[x][0] for x in newtraits)

		return chain(tclear, tset)

	@staticmethod
	def change_text_traits(style_codes, index, traits):
		return (style_codes[x][index] for x in traits)

	def select_transition(self,
			former:types.RenderParameters,
			latter:types.RenderParameters
		) -> Iterable[bytes]:
		"""
		# Construct SGR codes necessary to transition the SGR state from &former to &latter.

		# Usually called through &transition_render_parameters.
		"""

		if former == latter:
			# Identical; no transition.
			return

		# text traits
		current = former[0]
		target = latter[0]
		if current != target:
			yield from self.transition_traits(self.style_codes, current, target)

		# text color
		current = former[1]
		target = latter[1]
		if current != target:
			yield from self.select_color('text', target)

		# cell color
		current = former[2]
		target = latter[2]
		if current != target:
			yield from self.select_color('cell', target)

		# line color
		current = former[3]
		target = latter[3]
		if current != target:
			yield from self.select_color('line', target) #* No tty-16 colors!

	def transition_render_parameters(self, former, latter):
		return self.csi_filter_empty(b'm', *self.select_transition(former, latter))

	def reset_render_parameters(self, state):
		return self.csi(b'm',
			self.cached_integer_encode(0),
			*self.select_color('text', state.textcolor),
			*self.select_color('cell', state.cellcolor),
			*self.change_text_traits(state.traits),
		)

	def __init__(self,
			encoding,
			errors='surrogateescape',
			integer_encode_cache_size=32,
			word_encode_cache_size=32,
		):

		self.encoding = encoding

		ef = codecs.getencoder(encoding) # standard library codecs
		self._encoder = ef

		def ttype_encode(obj, errors=errors, str=str, ef=ef):
			return ef(str(obj), errors)[0] # str.encode(&encoding)

		# Direct encoder access.
		self.encode = ttype_encode

		# XXX: refer to cache handle rather than functools.lru_cache directly
		self.cached_integer_encode = functools.lru_cache(integer_encode_cache_size)(ttype_encode)
		self.cached_words_encode = functools.lru_cache(word_encode_cache_size)(ttype_encode)

		umethod = self.__class__.transition_render_parameters
		self.cached_transition = (functools.lru_cache(16)(umethod))

# The default terminal type used by &Context.
utf8_terminal_type = Type('utf-8')

class Context(object):
	"""
	# Rendering Context for character matrices.

	# Initialized using the terminal &Type that designates how escape sequences should be serialized.

	# Methods beginning with (id)`context_` are Context configuration interfaces
	# returning the instance for method chaining. After creating a &Context instance,
	# some of them may need to be called for proper usage:

		# - &context_set_position
		# - &context_set_dimensions
		# - &context_set_text_color
		# - &context_set_cell_color

	# Majority of methods return &bytes or iterables of &bytes that should be sent
	# to the terminal to cause the desired effect.

	# [ Elements ]
	# /RenderParameters/
		# Type containing data used to render &Text with the configured attributes.
	# /Phrase/
		# Sequence of &Words type. The primary interest of higher-level methods on &Context.
		# Passed to &render and &print.
	# /Words/
		# Named type annotation describing the contents of a &Phrase.
	# /Page/
		# Named type annotation for a sequence of &Phrase.
	# /Text/
		# Alias to the builtin &str.
	# /normal_render_parameters/
		# A &RenderParameters instance containing the default text and cell color without
		# any &Traits.
	"""

	# Provide context instance relative access for allowing overloading and convenience.
	# The types may be overridden globally by patching &.types prior to importing &.matrix.
	from .types import \
		Text, \
		Traits, \
		RenderParameters, \
		Words, \
		Phrase, \
		Page

	control_mapping = {chr(i): chr(0x2400 + i) for i in range(32)}
	control_table = str.maketrans(control_mapping)

	@staticmethod
	@functools.lru_cache(32)
	def translate(spoint, point):
		return (point[0] + spoint[0], point[1] + spoint[1])

	point = (None, None)
	dimensions = (None, None)
	width = height = None
	def __init__(self, type=utf8_terminal_type):
		self.terminal_type = type

		self._transition = functools.partial(type.cached_transition, type)
		self._csi = type.csi
		self._osc = type.osc
		self._csi_filter_empty = type.csi_filter_empty

		self._context_text_color = -1024
		self._context_cell_color = -1024
		self._context_line_color = -1024
		self._context_cursor = (0, 0)

		self.encode = type.cached_integer_encode

	@property
	def _context_traits(self):
		return self.RenderParameters((
			self.Traits(0),
			self._context_text_color,
			self._context_cell_color,
			self._context_line_color,
		))

	@property
	def context_render_parameters(self):
		return self.RenderParameters((
			self.Traits.none(),
			self._context_text_color,
			self._context_cell_color,
			self._context_line_color,
		))

	def context_set_position(self, point:tuple[int, int]):
		"""
		# Designate the absolute positioning of the character matrix.
		# Appropriate interface to use to set &self.point.
		"""
		self.point = point
		return self

	def context_set_dimensions(self, dimensions):
		"""
		# Designate the width and height of the character matrix being targeted.
		# Initializes &Context.dimensions, &width, and &height.
		"""
		self.width, self.height = dimensions
		self.dimensions = dimensions
		return self

	def context_set_text_color(self, color_id):
		"""
		# Configure the default text color.
		# Used by &reset_text and &reset_text_color.
		"""
		self._context_text_color = color_id
		return self

	def context_set_cell_color(self, color_id):
		"""
		# Configure the default cell color.
		# Used by &reset_text and &reset_cell_color.
		"""
		self._context_cell_color = color_id
		return self

	def context_set_line_color(self, color_id):
		"""
		# Configure the default line color.
		# Used by &reset_text and &reset_line_color.
		"""
		self._context_line_color = color_id
		return self

	def draw_unit_vertical(self, character):
		e = self.encode
		if not character:
			return b''

		c = e(character)
		c += self.seek_next_column()

		return c

	def draw_unit_horizontal(self, character):
		return self.encode(character)

	def draw_segment_vertical(self, unit, length):
		e = self.encode
		h, v = self.translate(self.point, self._context_cursor)
		c = e(unit)
		return b''.join([self.seek_absolute((h, v+i)) + c for i in range(length)])

	def draw_segment_horizontal(self, unit, length):
		return self.draw_unit_horizontal(unit) * length

	def set_text_color(self, color:int):
		"""
		# Construct the escape sequence for selecting a different text (foreground) color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('text', color))

	def set_cell_color(self, color:int):
		"""
		# Construct the escape sequence for selecting a different cell (background) color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('cell', color))

	def set_line_color(self, color:int):
		"""
		# Construct the escape sequence for selecting a different line (underline) color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('line', color))

	def set_render_parameters(self, rp:RenderParameters):
		return self._transition((None, None, None), rp)

	def reset_text_color(self):
		"""
		# Use the text color configured with &context_set_text_color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('text', self._context_text_color))

	def reset_cell_color(self):
		"""
		# Use the cell color configured with &context_set_cell_color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('cell', self._context_cell_color))

	def reset_line_color(self):
		"""
		# Use the cell color configured with &context_set_cell_color.
		"""
		return self._csi(b'm', *self.terminal_type.select_color('line', self._context_line_color))

	def reset_colors(self):
		"""
		# Using the cell and text colors stored on the Context, &self, construct
		# a sequence to instruct the terminal to use those colors.
		"""
		return self._csi(b'm', *(
			self.terminal_type.select_color('text', self._context_text_color) + \
			self.terminal_type.select_color('cell', self._context_cell_color) + \
			self.terminal_type.select_color('line', self._context_line_color)
		))

	def reset_text(self):
		"""
		# Reset text traits and colors.
		"""
		return self._csi(b'm', *(
			(b'0',) + \
			self.terminal_type.select_color('text', self._context_text_color) + \
			self.terminal_type.select_color('cell', self._context_cell_color) + \
			self.terminal_type.select_color('line', self._context_line_color)
		))

	def draw_words(self, phrasewordtext, control_map=control_table):
		"""
		# Translate the given &phraseword with &control_map and encode it
		# with the Context's configured encoding.
		"""

		return self.terminal_type.encode(phrasewordtext.translate(control_map))

	def render(self, phrase:Phrase, rparams:RenderParameters=None) -> Iterable[bytes]:
		"""
		# Render the given &phrase for display on the terminal.
		# Unlike most Context methods, &render returns an iterator
		# producing the sequences necessary to represent the phrase.

		# [ Parameters ]
		# /phrase/
			# The sequence of words to render. The text of the word must
			# be retrievable at (index)`1` and the rendering parameters
			# must be retrievable at (index)`2`.
		# /rparams/
			# If &None is given, the configured text and cell colors are used for
			# identifying the initial transition into the Phrase.
			# When rendering multiple &Phrase instances, the final triple of a phrase can be
			# provided to the next render call to make minimal transitions.
		"""

		e = self.terminal_type.encode
		transition = self._transition

		if rparams is None:
			last = self._context_traits
		else:
			last = rparams

		for words in phrase:
			# Don't bother catenating the strings; allows for style stripping.
			w, to = words[1:3]
			yield transition(last, to)
			last = to
			yield e(w)

	def print(self,
			phrases:Page,
			cellcounts:Sequence[int],
			indentations:Sequence[int]=itertools.repeat(0),
			width=None,
			zip=zip
		) -> Iterable[bytes]:
		"""
		# Print the page of phrases using &render.

		# Text Properties will be unconditionally reset, and lines will
		# be presumed dirty causing a following erase to be emitted after
		# the phrase is rendered.

		# &print, tentatively, expects the cursor to be at the desired starting location and
		# that the number of &phrases not exceed the &height of the context.

		# [ Parameters ]
		# /phrases/
			# The &Phrase instances that populate each line in the page.
		# /cellcounts/
			# The result of the corresponding &Phrase.cellcount method.
			# Usually cached alongside &phrases.
		# /indentation/
			# An optional sequence of integers specifying the leading empty cells
			# that should be used to indent the corresponding &Phrase.
			# If &Phrase instances manage their own indentation, this should normally be ignored.
		# /width/
			# Optional width override. Defaults to &self.width.
		"""

		rst = self.reset_text()
		nl = self.seek_next_line
		erase = self.erase
		render = self.render
		indent = self.spaces

		width = width or self.width
		adjustment = 0
		assert width is not None and width >= 0 #:Rendering Context misconfigured or bad &width parameter.

		yield rst

		for x, cc, ic in zip(phrases, cellcounts, indentations):
			if ic:
				# Don't bother with sequence alignment for print.
				# Skip the yield if there's nothing to yield.
				yield indent(ic)
				cc += ic

			adjustment = (width - cc) - 1
			if adjustment < 0:
				# Cells exceeds width.
				yield b''.join(render(x.rstripcells(-adjustment)))
				yield rst + nl()
			else:
				# Width exceeds cells.
				yield b''.join(render(x))
				yield rst + erase(adjustment) + nl()

	def spaces(self, count):
		"""
		# Construct a sequence or characters necessary for writing &count spaces.
		# Uses REP.
		"""
		if count == 0:
			return b''

		return b' ' + self._csi(b'b', self.encode(count-1))

	def clear_line(self, lineno):
		return self.seek_line(lineno) + self.clear_current_line()

	def clear_to_line(self, lineno=1):
		return self._csi(self.encode(lineno) + b'J')

	def clear_to_bottom(self):
		return self._csi(b'J')

	def clear_before_cursor(self):
		return self._csi(b'K', 1)

	def clear_after_cursor(self):
		return self._csi(b'K')

	def clear_current_line(self):
		return self.clear_before_cursor() + self.clear_after_cursor()

	def clear(self):
		"""
		# Clear the area according to its configured width and default text properties.

		# Text properties will be reset; the cell color configured on the context will be used.
		"""
		width = self.width

		init = self.seek_absolute(self.translate(self.point, (0, 0)))
		init += self.reset_text() # Make sure cell color is correct.

		clearline = self.erase(width)
		nl = self.seek_vertical_relative(1)

		return init + (self.height * (clearline + nl))

	def erase(self, count):
		"""
		# Erase the given &count of characters after the cursor.
		# Cursor position should be unchanged after the erase.

		# This should respect the current cell color, but disregard traits like underline.
		"""

		if count == 0:
			return b''

		return self._csi(b'X', self.encode(count))

	def replicate(self, vstart, vend, vto, page=(1,1)):
		"""
		# Replicate the area identified by &vstart and &vend to the position
		# identified by &vto.
		"""
		tvs = self.translate(self.point, vstart)
		tve = self.translate(self.point, vend)
		tvt = self.translate(self.point, vto)

		return self.terminal_type.replicate(
			(tvs[0]+1, tvs[1]+1),
			(tve[0], tve[1]),
			(tvt[0]+1, tvt[1]+1),
			page = page,
		)

	def confine(self):
		"""
		# Adjust the margins of the terminal to isolate the context's area.
		"""
		l, t = self.point
		s = b''
		s += self._csi(b's', self.encode(l+1), self.encode(l+self.dimensions[0]))
		s += self._csi(b'r', self.encode(t+1), self.encode(t+self.dimensions[1]))
		return s

	def scroll(self, lines:int):
		"""
		# Scroll forwards if quantity is positive or zero, backwards if negative.

		# [ Returns ]
		# The sequences to perform the scroll operation or an empty string
		# if the &lines count is zero.
		"""
		if lines < 0:
			return self.terminal_type.scroll_down(-lines)
		elif lines > 0:
			return self.terminal_type.scroll_up(lines)
		else:
			return b''

	def seek_absolute(self, coordinates) -> bytes:
		"""
		# Primitive absolute seek; Context cursor poisition is *not* updated.
		"""
		h, v = coordinates
		return self._csi(b'H', self.encode(v+1), self.encode(h+1))

	def seek_horizontal_relative(self, cells) -> bytes:
		"""
		# Primitive relative seek; Context cursor position is *not* updated.
		"""
		if cells < 0:
			return self._csi(b'D', self.encode(-cells))
		elif cells > 0:
			return self._csi(b'C', self.encode(cells))
		else:
			return b''

	def seek_vertical_relative(self, cells) -> bytes:
		"""
		# Primitive relative seek; Context cursor position is *not* updated.
		"""
		if cells < 0:
			return self._csi(b'A', self.encode(-cells))
		elif cells > 0:
			return self._csi(b'B', self.encode(cells))
		else:
			return b''

	def seek_first(self):
		"""
		# Seek the first cell in the Context.

		# Requires prior &context_set_position.
		"""
		return self.seek((0,0))

	def seek_last(self):
		"""
		# Seek the last cell in the Context.

		# Requires prior &context_set_dimensions.
		"""
		h, v = self.dimensions
		return self.seek((h-1, v-1))

	def seek(self, point):
		"""
		# Seek to the point relative to the area and store the point on the context.
		"""
		self._context_cursor = point
		return self.seek_absolute(self.translate(self.point, point))

	def tell(self):
		return self._context_cursor

	def seek_bottom(self):
		"""
		# Seek to the last row of the area and the first column.
		"""
		return self.seek((0, self.height-1))

	def seek_start_of_line(self):
		"""
		# Seek to the start of the line.
		"""
		return self.seek((0, self._context_cursor[1]))

	def seek_line(self, lineno):
		"""
		# Seek to the beginning of a particular line number.
		"""
		return self.seek((0, lineno))

	def seek_next_line(self):
		"""
		# Seek beginning of next line.
		"""
		return self.seek((0, self._context_cursor[1]+1))

	def seek_next_column(self):
		h, v = self._context_cursor
		return self.seek((h, v+1))

	def seek_relative(self, rcoords):
		"""
		# Seek the relative coordinates and update the Context's cursor.
		"""
		h, v = rcoords
		self._context_cursor = (h+self._context_cursor[0], v+self._context_cursor[1])
		return self.seek_horizontal_relative(h) + self.seek_vertical_relative(v)

class Screen(Context):
	"""
	# Matrix &Context bound to the first column and row.

	# Screens are given a slightly wider scope than &Context and provides
	# access to some configuration options that are not always maintained
	# for the duration of the process.
	"""
	point = types.Point((0,0))

	def set_window_title_text(self, title):
		"""
		# Instruct the emulator to use the given title for the window.
		# The given &title should be plain text and control characters will be translated.
		"""
		return self.terminal_type.wm_title(title.translate(self.control_table))

	def report_cursor_position(self):
		"""
		# Request that the terminal report the cursor position.
		"""
		return self._csi(b"n", b"6")

	def report_device_status(self):
		"""
		# Request that the terminal report status.
		"""
		return self._csi(b"n", b"5")

	def set_cursor_visible(self, visible):
		"""
		# Adjust cursor visibility.
		"""
		if visible:
			return self.terminal_type.decset((25,))
		else:
			return self.terminal_type.decrst((25,))

	def set_cursor_blink(self, blinking):
		"""
		# Adjust cursor blink state.
		"""
		if blinking:
			return self.terminal_type.decset((12,))
		else:
			return self.terminal_type.decrst((12,))

	def reset(self):
		"""
		# Construct a soft terminal reset.
		"""
		return self._csi(b'!p')

	def set_scrolling_region(self, top, bottom):
		"""
		# Confine the scrolling area to the given rows.
		"""
		return self._csi(b'r', self.encode(top+1), self.encode(bottom+1))

	def reset_scrolling_region(self):
		"""
		# Set the scrolling region to the entire screen.
		"""
		return self._csi(b'r')

	def open_scrolling_region(self, top:int, bottom:int):
		"""
		# Set the scrolling region, enter it, and seek the bottom.
		# Subsequent &exit_scrolling_region and &enter_scrolling_region
		# should be use to maintain the SR's state.
		"""
		sr = self.set_scrolling_region(top, bottom)
		en = self.terminal_type.decset((self.terminal_type._pm_origin,))
		return self.store_cursor_position() + sr + en + self.restore_cursor_position()

	def close_scrolling_region(self):
		"""
		# Save the screen buffer, reset the scrolling region, and restore the buffer.
		# This preserves the screen's state after the transition.
		"""
		ttype = self.terminal_type
		return self.store_cursor_position() + ttype.decset((ttype._pm_screen,)) + \
			self.reset_scrolling_region() + \
			ttype.decrst((ttype._pm_screen,)) + self.enter_scrolling_region()

	def store_cursor_position(self):
		"""
		# Emulator level cursor storage.
		"""
		return self.terminal_type.esc(b'7')
		# Prefer the DEC form to avoid conflict with DECSLRM.
		# return self._csi(b's')
	store_cursor_location = store_cursor_position

	def restore_cursor_position(self):
		"""
		# Restore cursor positionn saved by &store_cursor_position.
		"""
		return self.terminal_type.esc(b'8')
		# return self._csi(b'u')
	restore_cursor_location = restore_cursor_position

	def enter_scrolling_region(self):
		"""
		# Enter scrolling region; normal terminal output; restores cursor location.
		"""
		return \
			self.terminal_type.decset((self.terminal_type._pm_origin,)) + \
			self.restore_cursor_position()

	def exit_scrolling_region(self):
		"""
		# Exit scrolling region; allow out of region printing; saves cursor location.
		"""
		return \
			self.store_cursor_position() + \
			self.terminal_type.decrst((self.terminal_type._pm_origin,))

	def clear(self):
		return self.reset_text() + self._csi(b'H') + self._csi(b'2J')
