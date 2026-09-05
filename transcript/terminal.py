"""
# Terminal support for status displays.
"""
import os
import io
import typing
import itertools
import collections
from collections.abc import Sequence, Mapping

from ..context import tools
from ..status import frames

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

@tools.struct()
class Transaction(object):
	order: Sequence[tuple[str, str]]
	formats: Sequence[tuple[str, str, str, object]]
	types: Mapping[str, str]

	def __iter__(self):
		for o, f in zip(self.order, self.formats):
			yield *o, *f

test_transactions = Transaction(
	# order
	[
		('executing', 'work.w_executing'),
		('usage', 'usage.r_process'),
		('passed', 'work.w_executed'),
		('skipped', 'work.w_granted'),
		('failed', 'work.w_failed'),
	],

	# formats
	[
		('x', "executing", 'orange', tools.partial(r_count, 'executing')),
		('u', "usage", 'violet', tools.partial(r_count, 'usage')),
		('p', "passed", 'green', tools.partial(r_count, 'passed')),
		('s', "skipped", 'blue', tools.partial(r_count, 'skipped')),
		('f', "failed", 'red', tools.partial(r_count, 'failed')),
	],

	# types
	{
		'usage': 'rate_window',
	},
)

process_transactions = Transaction(
	# order
	[
		('executing', 'work.w_executing'),
		('usage', 'usage.r_process'),
		('cached', 'work.w_granted'),
		('failed', 'work.w_failed'),
		('processed', 'work.w_executed'),
	],

	# formats
	[
		('x', "executing", 'orange', tools.partial(r_count, 'executing')),
		('u', "usage", 'violet', tools.partial(r_count, 'usage')),
		('c', "cached", 'blue', tools.partial(r_count, 'cached')),
		('f', "failed", 'red', tools.partial(r_count, 'failed')),
		('p', "processed", 'green', tools.partial(r_count, 'processed')),
	],

	# types
	{
		'usage': 'rate_window',
	}
)

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

class Theme(object):
	"""
	# The rendering methods and parameters used by a &Status.
	"""

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

	def _render(self, phrase):
		for color, text in phrase:
			yield b'\x1b[' + self._styles[color] + b'm' + \
				text.encode('utf-8') + \
				b'\x1b[39m'

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

	def define(self, name, style, label=None, path=()):
		"""
		# Define the &style to use with the given &name.
		"""
		self.stylesets[name] = style
		if label:
			self.labels[name] = label
		if path:
			self.paths[name] = path.split('.')

	def implement(self, type, render):
		"""
		# Assign a render method, &call, for the &field.
		"""
		self.rendermethod[type] = render

	def __init__(self, fields):
		self.fields = fields
		self.stylesets = {}
		self.labels = {}
		self.paths = {}
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
		return list(self.style(r_method(field)))

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

	def __init__(self, theme:Theme):
		self.theme = theme # Style sets and value rendering methods.
		self.metrics = None
		self.view = {} # Field view identifying value filtering (rate vs total).

		# Status local:
		self._title = None
		self._prefix = None
		self._suffix = None

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

		self._prefix = list(words)

	def suffix(self, *words):
		"""
		# Attach a constant phrase to the end of the monitor.
		"""

		self._suffix = list(words)

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

	def render(self, filter=(lambda x: False)):
		render = self.theme.render
		metrics = self.metrics

		label = render('Label', "duration")
		value = render('duration', self.duration() / (10**9))
		yield 'total', label, value

		for k in self.theme.fields:
			utype = self.view.get(k, 'total')
			readv = getattr(self, utype)
			try:
				v = readv(self.theme.paths[k])
			except ZeroDivisionError:
				utype = 'total'
				v = self.total(self.theme.paths[k])

			if filter(v):
				continue
			value = render(k, v)
			label = render('Label', self.theme.labels[k])

			yield utype, label, value

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
		fseps = map(n, ' ' * (len(phrases)-1))

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
				ph = [('default', self._title[0] + ': ')]
			elif context:
				ph = [('default', context + ': ')]
			else:
				ph = []

			ph.extend(self.snapshot())
			return ph
		finally:
			self.view = sv

	def message(self, identifier):
		syn = self.synopsis(identifier)
		return b''.join(self.theme._render(syn)).decode('utf-8')

	def frame(self, type, identifier, channel=None):
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

		return frames.compose(type, self.message(identifier), channel, ext)

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

def r_title(value):
	"""
	# Render method for monitor titles.
	"""

	category, dimensions = value
	t = str(category)
	if dimensions:
		t += '[' + ']['.join(dimensions) + ']'
	return [('plain', t)]

def form(xact):
	"""
	# Construct a &Theme from the provided order and formatting structures.
	"""

	t = Theme([k[0] for k in xact]).configure()
	t.implement('duration', Theme.r_duration)
	t.implement('title', r_title)

	t.define('Label-Separator', 'dark')
	t.define('duration', 'white')
	t.define('unit-label', 'gray')
	t.define('data-rate-receive', 'default')
	t.define('data-rate-transmit', 'default')
	t.define('data-rate', 'gray')

	for k, path, keycode, label, color, fn in xact:
		if fn is not None:
			t.implement(k, fn)
		t.define(k, color, label, path)

	return t, getattr(xact, 'types', {})

def aggregate(xact, lanes=1):
	"""
	# Construct &Status instances for formatting frames using the theme &xact.

	# Returns a sequence of &Status instances for the dimensions
	# and a single Status for the aggregation.
	"""

	t, types = form(xact)
	lanes_seq = [Status(t) for i in range(lanes)]
	m = Status(t)

	for k, v in types.items():
		m.set_field_read_type(k, v)
		for x in lanes_seq:
			x.set_field_read_type(k, v)

	return lanes_seq, m
