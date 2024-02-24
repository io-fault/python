"""
# Terminal support for status displays.
"""
import os
import io
import typing
import itertools
import collections

from ..context import tools
from ..status import frames

def duration_repr(seconds) -> typing.Tuple[float, str]:
	if seconds < 90:
		# seconds, minute and a half
		return (seconds / 1.0, 's')

	minutes = seconds / 60
	if minutes < 90:
		# minutes, hour and a half
		return (seconds / 60, 'm')

	hours = minutes / 60
	if hours < 240:
		return (hours, 'h')

	days = hours / 24
	return (days, 'd')

class Phrase(list):
	__slots__ = ()

	def cellcount(self):
		return sum(len(x[1]) for x in self)

class Legacy(object):
	"""
	# Abstraction for legacy ANSI/DEC escapes.
	"""

	_escape = b'\x1b'
	_csi_open = _escape + b'['
	_pm_open = _csi_open + b'?'
	_pm_save = _pm_open + b'6;1049s'
	_pm_restore = _pm_open + b'6;1049r'
	_pm_origin_set = _pm_open + b'6h'
	_pm_origin_reset = _pm_open + b'6l'
	_pm_screen_set = _pm_open + b'1049h'
	_pm_screen_reset = _pm_open + b'1049l'
	_pm_show_cursor = _pm_open + b'25h'
	_pm_hide_cursor = _pm_open + b'25l'
	_restore_cursor = _escape + b'8'
	_store_cursor = _escape + b'7'
	_nl = _csi_open + b'1B'
	_reset_sgr = _csi_open + b'0;39;49;59m'

	_styles = {
		'default': b'39',
		'black': b'30',
		'red': b'31',
		'green': b'32',
		'yellow': b'33',
		'blue': b'34',
		'magenta': b'35',
		'cyan': b'36',
		'white': b'37',

		'orange': b'38;5;208',
		'violet': b'38;5;135',
		'teal': b'38;5;23',
		'purple': b'38;5;93',
		'dark': b'38;5;236',
		'gray': b'38;5;241',
	}
	_reset_text = _csi_open + _styles['default'] + b'm'

	@classmethod
	def _join(Class, *i:int, _sep=';'):
		return _sep.join(map(str, i)).encode('ascii')

	def __init__(self, encoding='utf-8'):
		self.encoding = encoding
		self.dimensions = (0, 0)
		self._lines = 0
		self._width = 0
		self._height = 0
		self._offset = -1
		self._seek = b''

	def set_cursor_visible(self, visible):
		"""
		# Adjust cursor visibility.
		"""

		if visible:
			return self._pm_show_cursor
		else:
			return self._pm_hide_cursor

	def set_scrolling_region(self, top:int, bottom:int):
		"""
		# Confine the scrolling region to the given rows.
		"""

		return self._csi_open + self._join(top+1, bottom+1) + b'r'

	def reset_scrolling_region(self):
		"""
		# Release confinements on scrolling region.
		"""

		return self._csi_open + b'r'

	def open_scrolling_region(self, top:int, bottom:int):
		"""
		# Set the scrolling region, enter it, and seek the bottom.
		# Subsequent &exit_scrolling_region and &enter_scrolling_region
		# should be use to maintain the SR's state.
		"""

		sr = self.set_scrolling_region(top, bottom)
		return self._store_cursor + sr + self._pm_origin_set + self._restore_cursor

	def close_scrolling_region(self):
		"""
		# Save the screen buffer, reset the scrolling region, and restore the buffer.
		# This preserves the screen's state after the transition.
		"""

		return self._store_cursor + self._pm_screen_set + \
			self.reset_scrolling_region() + \
			self._pm_screen_reset + self.enter_scrolling_region()

	def enter_scrolling_region(self):
		"""
		# Enter scrolling region; normal terminal output; restores cursor location.
		"""

		return \
			self._pm_origin_set + \
			self._restore_cursor

	def exit_scrolling_region(self):
		"""
		# Exit scrolling region; allow out of region printing; saves cursor location.
		"""

		return \
			self._store_cursor + \
			self._pm_origin_reset

	def clear(self):
		"""
		# Clear the staionary area according to its configured width and default text properties.
		"""

		clearline = self._csi_open + self._join(self._width) + b'X'
		return self._seek + (self._height * (clearline + self._nl))

	def erase(self, area):
		"""
		# Erase the given area.
		"""

		clearline = self._csi_open + self._join(area[3]) + b'X'
		return self.seek(area, 0, 0) + clearline

	def seek(self, monitor, top_offset, left_offset) -> bytes:
		"""
		# Primitive relative seek; Context cursor position is *not* updated.
		"""

		top = monitor[0]
		left = monitor[1]
		return self._csi_open + self._join(top + top_offset + 1, left + left_offset + 1) + b'H'

	def style(self, name:str, text:str):
		"""
		# Style the given &text as &name.

		# Text color will be reset to the default.
		"""

		return self._csi_open + self._styles[name] + b'm' + text.encode(self.encoding) + self._reset_text

	def render(self, phrase):
		"""
		# Translate the color names to SGR codes.
		"""

		for color, text in phrase:
			yield self.style(color, text)

	def configure(self, height, width, lines):
		"""
		# Update the dimensions of the screen.
		"""

		self.dimensions = (height, width)
		self._width = width
		self._height = lines
		self._offset = height - lines
		self._seek = self._csi_open + self._join(self._offset+1, 1) + b'H'

	@property
	def position(self):
		return (self._offset, 0)

class Layout(object):
	"""
	# The set, sizes, and ordering of fields present in a monitor.
	"""

	# Identifier-width(cell count) pairs.
	Definition = typing.Tuple[str, int]
	Fields = typing.Sequence[Definition]

	@staticmethod
	def separators(fields:int, termination=".", separation=", "):
		"""
		# Generate a series of separators finished with a terminator.
		# Given a number of a fields, emit separators until the final index
		# is reached.
		"""

		for x in range(fields-1):
			yield separation

		yield termination

	def label(self, field, text:str):
		"""
		# The display text for the field's label.
		"""
		self.labels[field] = text

	def __init__(self, fields:Fields, **updates):
		self.labels = {}
		self.order = [x[0] for x in fields]
		self.paths = [tuple(x[1].split('.')) for x in fields]
		self.cells = {x[0]: x[2] for x in fields}
		self.cells.update(updates.items())

	def fields(self):
		"""
		# Iterate over the fields in their designated order along with separators
		# that can be used to follow the rendered field.
		"""
		return zip(self.order, self.paths, self.separators(len(self.order)))

	def positions(self):
		"""
		# Join the field identifier, cell allocation, and field label in
		# the order designated by &order.
		"""
		fl = self.labels
		cc = self.cells

		for fid in self.order:
			yield (fid, fl[fid], cc[fid])

class Theme(object):
	"""
	# The rendering methods and parameters used by a &Status.
	"""

	Formatter = tuple[str, str]

	def default_render_method(self, key, field):
		"""
		# Renders the string form of &field with the style set identified
		# by &key.
		"""
		return [
			('plain' if key not in self.stylesets else key, str(field)),
		]

	@staticmethod
	def r_transparent(value:typing.Sequence[Formatter]):
		"""
		# Render method expecting and returning a sequence of formatting pairs.

		# Used in cases where the field wishes to control theme-relative
		# formatting directly.
		"""
		return list(value)

	@staticmethod
	def r_duration(value):
		"""
		# Render method for common duration fields.
		"""
		time, precision = duration_repr(value)
		string = "{:.1f}".format(value)

		return [
			('duration', string),
			(precision+'-timeunit', precision),
		]

	def define(self, name, style):
		"""
		# Define the &style to use with the given &name.
		"""
		self.stylesets[name] = style

	def implement(self, type, render):
		"""
		# Assign a render method, &call, for the &field.
		"""
		self.rendermethod[type] = render

	def __init__(self):
		self.stylesets = {}
		self.rendermethod = {}

	def configure(self):
		self.stylesets.update({
			# Time is expected to be common among all themes.
			'plain': 'default',
			's-timeunit': 'blue',
			'm-timeunit': 'yellow',
			'h-timeunit': 'orange',
			'd-timeunit': 'red',
			'Label': 'gray',
			'Label-Emphasis': 'white',
		})
		return self

	def style(self, celltexts:typing.Sequence[Formatter]):
		"""
		# Emit words formatted according to their associated style set.
		"""

		idx = self.stylesets
		for style_idx, text in celltexts:
			yield (idx[style_idx], text)

	def render(self, type, field, *, partial=tools.partial):
		"""
		# Render the given &field according to the configured &type' render method.
		"""

		r_method = self.rendermethod.get(type) or partial(self.default_render_method, type)
		return Phrase(self.style(r_method(field)))

class Status(object):
	"""
	# Allocated area for status display of a set of changing fields.
	"""

	view_state_loop = {
		'total': 'rate_window',
		'rate_window': 'rate_overall',
		'rate_overall': 'total',
	}

	unit_type_separators = {
		'total': '+',
		'rate_window': '<',
		'rate_overall': '^',
	}

	def __init__(self, theme:Theme, layout:Layout, position):
		self.theme = theme # Style sets and value rendering methods.
		self.layout = layout # Field Ordering and Width
		self.context = position # Screen Context
		self.metrics = None
		self.view = {} # Field view identifying value filtering (rate vs total).

		# Status local:
		self._title = None
		self._prefix = None
		self._suffix = None
		self._update_field_cache()

	def _calculate_fields(self, alignment=1):
		position = 0
		trender = self.theme.render

		for fid, flabel, cells in self.layout.positions():
			rlabel = trender('label-'+fid, flabel)
			lc = rlabel.cellcount()
			usage = abs(cells) + lc + 2
			yield (position, cells, lc)

			indents, r = divmod(usage, alignment)
			position += (indents * alignment)
			if r != 0:
				position += alignment

		yield (position, 0, 0)

	def _update_field_cache(self):
		self._positions = list(self._calculate_fields())
		self._pcache = {
			k: (path, fpad, position, cells, lc)
			for (k, path, fpad), (position, cells, lc) in zip(self.layout.fields(), self._positions)
		}

	def reset(self, time, metrics):
		"""
		# Reset the metrics records using the given entry as the only one.
		"""
		self.metrics = [(time, metrics)]

	@property
	def current(self):
		return self.metrics[-1][1]

	def elapse(self, time):
		"""
		# Update the time field on the last metrics record.
		"""
		cur = self.metrics[-1][0]
		if cur == time:
			return
		self.metrics[-1] = (time, self.metrics[-1][1])

	def update(self, time, metrics, window=8*(10**9)):
		"""
		# Update the metrics record for the given point in time.
		"""
		self.metrics.append((time, metrics))

		cutoff = time - window
		for i, x in enumerate(self.metrics, 1):
			if x[0] > cutoff:
				del self.metrics[1:i]
				break

	def duration(self):
		return (self.metrics[-1][0] - self.metrics[0][0])

	def cycle(self, field):
		"""
		# Select the next read type for the given field using the &view_state_loop.
		"""

		units = self.view.get(field, 'total')
		next = self.view_state_loop[units]
		self.view[field] = next

	def set_field_read_type(self, field, units):
		if units not in self.view_state_loop:
			raise ValueError(units)
		self.view[field] = units

	def prefix(self, *words):
		"""
		# Attach a constant phrase to the beginning of the monitor.
		"""

		self._prefix = Phrase(words)

	def suffix(self, *words):
		"""
		# Attach a constant phrase to the end of the monitor.
		"""

		self._suffix = Phrase(words)

	def title(self, title, *dimensions):
		"""
		# Assign the monitor's title and dimension identifiers.
		"""

		self._title = (title, dimensions)

	def window_period(self):
		"""
		# Calculate the current metrics window size.
		"""
		try:
			start = self.metrics[1][0]
		except IndexError:
			start = self.metrics[0][0]

		return self.metrics[-1][0] - start

	def origin(self, field):
		return self.metrics[0][1][field]

	def window_delta(self, field):
		if len(self.metrics) <= i:
			i=0

		start = self.metrics[i][1][field]
		stop = self.metrics[-1][1][field]
		return stop - start

	def edge(self, field, i=1):
		if len(self.metrics) <= i:
			i=0
		return self.metrics[i][1][field]

	def total(self, field):
		return self.metrics[-1][1][field]

	def rate_window(self, field):
		delta = self.total(field) - self.edge(field)
		return delta / self.window_period()

	def rate_overall(self, field):
		delta = self.total(field) - self.edge(field)
		return delta / self.duration()

	def render(self, filter=(lambda x: False), offset=58):
		render = self.theme.render
		layout = self.layout
		metrics = self.metrics

		label = render('Label', "duration")
		value = render('duration', self.duration() / (10**9))
		yield 'total', label, value, 40, 8 - value.cellcount()

		for (k, path, fpad), (position, cells, lc) in zip(layout.fields(), self._positions):
			utype = self.view.get(k, 'total')
			readv = getattr(self, utype)
			try:
				v = readv(path)
			except ZeroDivisionError:
				utype = 'total'
				v = self.total(path)

			if filter(v):
				continue
			value = render(k, v)

			lstr = layout.labels[k]
			ncells = value.cellcount()
			label = render('Label', lstr)

			yield utype, label, value, position + offset, (cells - ncells)

	def delta(self, fields, offset=58):
		render = self.theme.render
		labels = self.layout.labels
		metrics = self.metrics

		label = render('Label', "duration")
		value = render('duration', self.duration() / (10**9))
		yield 'total', label, value, 40, 8 - value.cellcount()

		fields = ((k, self._pcache[k]) for k in fields if k in self._pcache)
		for k, (path, fpad, position, cells, lc) in fields:
			utype = self.view.get(k, 'total')
			readv = getattr(self, utype)
			try:
				v = readv(path)
			except ZeroDivisionError:
				utype = 'total'
				v = self.total(path)

			value = render(k, v)
			lstr = labels.get(k, k)
			ncells = value.cellcount()
			label = render('Label', lstr)

			yield utype, label, value, position + offset, (cells - ncells)

	def phrase(self, filter=(lambda x: False)):
		"""
		# The monitor's image as a single phrase instance.
		"""
		phrases = list(self.render(filter=filter))
		utypes = (x[0] for x in phrases)
		labels = (x[1] for x in phrases)
		values = (x[2] for x in phrases)

		n = (lambda x: self.theme.render('Label-Separator', x))
		lseps = (n(self.unit_type_separators[x]) for x in utypes)
		fseps = map(n, self.layout.separators(len(phrases)))

		return tools.interlace(values, lseps, labels, fseps)

	def snapshot(self, *, Chain=itertools.chain.from_iterable):
		"""
		# A bytes form of the &Status.phrase. (The image without cursor movement)
		"""

		return Chain(self.phrase(filter=(lambda x: x in {0,0.0,"0"})))

	def profile(self):
		"""
		# Construct a triple containing the start and stop time and the final metrics.
		"""

		return (self.metrics[0][0], self.metrics[-1][0], self.metrics[-1][1])

	def synopsis(self, context=None, vmap={'rate_window':'rate_overall'}):
		"""
		# Construct a status frame synopsis using the monitor's configuration and metrics.
		"""

		sv = dict(self.view)
		try:
			for k, v in list(self.view.items()):
				self.view[k] = vmap.get(v, v)

			if context is None:
				ph = Phrase([('default', self._title[0] + ': ')])
			elif context:
				ph = Phrase([('default', context + ': ')])
			else:
				ph = Phrase()

			ph.extend(self.snapshot())
			return ph
		finally:
			self.view = sv

	def frame(self, control, type, identifier, channel=None):
		"""
		# Construct a transaction frame for reporting the status.
		# Used after the completion of the dispatcher.
		"""
		start, stop, metrics = self.profile()
		ext = {
			'@timestamp': [str(start)],
			'@duration': [str(stop - start)],
			'@metrics': [metrics.sequence()],
		}
		if identifier:
			ext['@transaction'] = [identifier]

		msg = control.render_status_text(self, identifier)
		return frames.compose(type, msg, channel, ext)

class Monitor(object):
	"""
	# Terminal display management for monitoring changes in &Status instances.
	"""

	def render_status_text(self, monitor, identifier) -> str:
		"""
		# Construct the string representation of the given &monitor' status.
		"""

		return b''.join(self.screen.render(monitor.synopsis(identifier))).decode(self.screen.encoding)

	def __init__(self, screen, fileno):
		self.screen = screen
		self._buffer = []
		self._fileno = fileno
		self._io = io.FileIO(fileno, closefd=False, mode='w')
		self._write = self._io.write

	def install(self, monitor):
		"""
		# Erase, reframe, and update the given monitor..
		"""

		self._buffer.append(self.screen.erase(monitor.context))
		self.frame(monitor)
		self.update(monitor, monitor.render())

	def frame(self, monitor, offset=0):
		"""
		# Render and emit the prefix, title, and suffix of the &monitor.

		# Operation is buffered and must be flushed to be displayed.
		"""

		context = monitor.context
		buf = self._buffer

		if monitor._prefix:
			offset = offset + monitor._prefix.cellcount() + 2
			buf.append(self.screen.seek(context, 0, 0))
			buf.extend(self.screen.render(monitor._prefix))

		ph = monitor.theme.render('title', monitor._title)
		buf.append(self.screen.seek(context, 0, offset))
		buf.extend(self.screen.render(ph))
		buf.append(b':')

		if monitor._suffix:
			buf.extend(self.screen.render(monitor._suffix))

	def update(self, monitor, fields, offset=0):
		"""
		# Render and emit the given &fields.

		# Operation is buffered and must be flushed to be displayed.
		"""

		context = monitor.context
		SR = self.screen.render
		R = monitor.theme.render
		chain = itertools.chain.from_iterable

		for utype, label, ph, position, pad in fields:
			lsep = R('Label-Separator', monitor.unit_type_separators[utype])
			i = chain([
				(self.screen.seek(context, 0, position + offset), b' ' * pad),
				SR(ph),
				SR(lsep),
				SR(label) if label else (),
			])
			self._buffer.append(b''.join(i))

	def flush(self):
		"""
		# Write any buffered terminal changes to the device.
		"""
		l = len(self._buffer)
		buf = bytearray()
		buf += self.screen.exit_scrolling_region()
		buf += self.screen.set_cursor_visible(False)
		for x in itertools.islice(self._buffer, 0, l):
			buf += x
		buf += self.screen.enter_scrolling_region()
		buf += self.screen.set_cursor_visible(True)

		try:
			self._write(buf)
		except:
			raise
		else:
			del self._buffer[:l]

	def clear(self):
		"""
		# Clear the entire status regions.
		"""

		self._buffer.append(self.screen.clear())

	def configure(self, lines:int):
		"""
		# Configure the scrolling region allocating &lines at
		# the top or bottom of the screen for status display.

		# This method should be called after window changes of any type.
		# The window size is refreshed from the device; monitors should
		# also be reallocated so that their Context positions can be adjusted.
		"""

		if not lines:
			raise ValueError("line allocation must be non-zero")

		from termios import tcgetwinsize
		height, width = tcgetwinsize(self._fileno)
		self.screen.configure(height, width, lines)

		init = b'\n' * lines + self.screen._csi_open + self.screen._join(lines) + b'A'
		init += self.screen.open_scrolling_region(0, (height-lines)-1)
		self._buffer.append(self.screen.clear())
		self._write(init)
		return self

	def _save(self):
		import atexit
		self._io.write(self.screen._pm_save)
		atexit.register(self._restore)

	def _restore(self):
		self._io.write(self.screen.close_scrolling_region() + self.screen._pm_restore)

_metric_units = [
	('', '', 0),
	('kilo', 'k', 3),
	('mega', 'M', 6),
	('giga', 'G', 9),
	('tera', 'T', 12),
	('peta', 'P', 15),
	('exa', 'E', 18),
	('zetta', 'Z', 21),
	('yotta', 'Y', 24),
]

def _precision(count):
	index = 0
	for pd in _metric_units:
		count //= (10**3)
		if count < 1000:
			return pd
	return pd

def _strings(value, formatting="{:.1f}".format):
	suffix, power = _precision(value)[1:]
	r = value / (10**power)
	return (formatting(r), suffix)

def r_count(field, value, isinstance=isinstance):
	"""
	# Render method for counts providing compression using metric units.
	"""

	if isinstance(value, str) or (value < 100000 and not isinstance(value, float)):
		n = str(value)
		unit = ''
	else:
		n, unit = _strings(value)

	if n == "0":
		# By default, don't color zeros.
		field = 'plain'

	return [
		(field, n),
		('unit-label', unit)
	]

def r_title(value):
	"""
	# Render method for monitor titles.
	"""

	category, dimensions = value
	t = str(category)
	if dimensions:
		t += '[' + ']['.join(dimensions) + ']'
	return [('plain', t)]

def form(module):
	"""
	# Construct a &Layout and &Theme from the provided order and formatting structures.
	"""

	l = Layout(module.order)
	t = Theme().configure()
	t.implement('duration', Theme.r_duration)
	t.implement('title', r_title)

	t.define('Label-Separator', 'dark')
	t.define('duration', 'white')
	t.define('unit-label', 'gray')
	t.define('data-rate-receive', 'default')
	t.define('data-rate-transmit', 'default')
	t.define('data-rate', 'gray')

	for (k, path, width), (keycode, label, color, fn) in zip(module.order, module.formats):
		if fn is not None:
			t.implement(k, fn)
		t.define(k, color)
		l.label(k, label or None)

	return t, l, getattr(module, 'types', {})

def identify_device(path='/dev/tty'):
	"""
	# Use the first three file descriptors to determine the
	# path to the tty device. If no path can be identified,
	# return the given &path which defaults to `/dev/tty`.
	"""

	for i in range(3):
		try:
			path = os.ttyname(i)
		except:
			continue
		else:
			break

	return path

def setup(device='/dev/tty'):
	screen = Legacy()
	fileno = os.open(device, os.O_RDWR)
	m = Monitor(screen, fileno)
	m._save()
	return m

def aggregate(control:Monitor, module, lanes=1, width=80):
	"""
	# Construct &Status instances allocated using &control for
	# displaying the aggregate of the dimension allocations.

	# Returns a sequence of &Status instances for the dimensions
	# and a single Status for the aggregation.
	"""

	top, left = control.screen.position
	t, l, types = form(module)
	lanes_seq = [
		Status(t, l, (top + i, left, 1, width))
		for i in range(lanes)
	]
	m = Status(t, l, (top + lanes, left, 1, width))

	for k, v in types.items():
		m.set_field_read_type(k, v)
		for x in lanes_seq:
			x.set_field_read_type(k, v)

	return lanes_seq, m
