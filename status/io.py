"""
# Transaction frame aggregation for process trees.
"""
import os
import sys
import signal
import io
import typing
import itertools
import collections
from collections.abc import Sequence, Mapping

from ..context import tools
from ..system import execution
from ..time import system as time

from . import frames

@tools.struct()
class Work:
	"""
	# Work unit progress metrics.

	# [ Properties ]
	# /w_prepared/
		# Number of Work Units that will be performed.
	# /w_failed/
		# Number of Work Units that indicated failure.
	# /w_granted/
		# Number of Work Units that were already considered complete.
		# Tests skipped or cached results.
	# /w_executed/
		# Number of Work Units executed that did not indicate failure.
	"""
	m_symbol = '%'

	w_prepared: int = 0
	w_executed: int = 0
	w_granted: int = 0
	w_failed: int = 0

	@property
	def w_total(self) -> int:
		"""
		# Number of failed, executed, or granted Works Units.
		"""
		return self.w_failed + self.w_executed + self.w_granted

	@property
	def w_executing(self) -> int:
		"""
		# Number of prepared work units that were not granted and
		# have not completed or failed.
		"""
		return self.w_prepared - self.w_total

	def __str__(self):
		return ''.join(map(str,
			[
				self.w_executed,
				'+', self.w_granted,
				'-', self.w_failed,
				'/', self.w_prepared,
			])
		)

	def empty(self) -> bool:
		if not (self.w_prepared, self.w_executed, self.w_granted, self.w_failed) == (0, 0, 0, 0):
			return False

		return True

	def __add__(self, op):
		return self.__class__(
			self.w_prepared + op.w_prepared,
			self.w_executed + op.w_executed,
			self.w_granted + op.w_granted,
			self.w_failed + op.w_failed,
		)

	@classmethod
	def split(Class, text:str):
		try:
			x, prepared = text.split('/', 1)
		except ValueError:
			prepared = None
		else:
			prepared = int(prepared)

		try:
			executed, x = x.split('+', 1)
		except ValueError:
			executed = x

		if executed[:1] == '#':
			executed = executed[1:]

		executed = int(executed)
		granted, failed = map(int, x.split('-', 1))

		return Class(prepared, executed, granted, failed)

@tools.struct()
class Advisory:
	"""
	# Advisory messaging metrics.

	# [ Properties ]
	# /m_notices/
		# Messages emitted by the Work Units that were neither warnings or errors.
	# /m_warnings/
		# Warnings issued by the Work Units to the Application.
	# /m_errors/
		# Errors issued by the Work Units to the Application.
	"""
	m_symbol = '@'

	m_notices: int = 0
	m_warnings: int = 0
	m_errors: int = 0

	@property
	def m_total(self) -> int:
		"""
		# Total number of errors, warnings, and notices.
		"""
		return self.m_errors + self.m_warnings + self.m_notices

	def __str__(self):
		return ''.join(map(str, [
			'', self.m_notices,
			"!", self.m_warnings,
			"*", self.m_errors,
		]))

	def empty(self) -> bool:
		return (self.m_notices, self.m_warnings, self.m_errors) == (0, 0, 0)

	def __add__(self, op):
		return self.__class__(
			self.m_notices + op.m_notices,
			self.m_warnings + op.m_warnings,
			self.m_errors + op.m_errors,
		)

	@classmethod
	def split(Class, text:str):
		p = []
		parts = [
			text.find('!'),
			text.find('*'),
			len(text),
		]

		x = 0
		for y in parts:
			if y == -1:
				y = parts[-1]
			p.append(int(text[x:y]))
			x = y + 1

		return Class(*p)

@tools.struct()
class Resource:
	"""
	# Resource usage metrics.

	# [ Properties ]
	# /r_divisions/
		# The number of system processes that used the measured resources.
	# /r_time/
		# The sum of the duration of all divisions.
	# /r_process/
		# Processor usage of the divisions.
	# /r_memory/
		# Memory usage of the divisions.
	"""
	m_symbol = '$'

	r_divisions: int = 0
	r_memory: int = 0
	r_process: int = 0
	r_time: int = 0

	def __str__(self) -> str:
		return ''.join([
			str(self.r_process),
			':', str(self.r_time),
			'#', str(self.r_memory),
			'/', str(self.r_divisions),
		])

	def empty(self) -> bool:
		return (self.r_divisions, self.r_memory, self.r_process, self.r_time) == (0, 0, 0, 0)

	def __add__(self, op):
		return self.__class__(
			self.r_divisions + op.r_divisions,
			self.r_memory + op.r_memory,
			self.r_process + op.r_process,
			self.r_time + op.r_time,
		)

	@classmethod
	def split(Class, text:str):
		p = []
		parts = [
			text.find(':'),
			text.find('#'),
			text.find('/'),
			len(text),
		]

		x = 0
		for y in parts:
			if y == -1:
				y = parts[-1]
			p.append(int(text[x:y]))
			x = y + 1

		return Class(p[-1], p[-2], p[0], p[1])

@tools.struct()
class Procedure:
	"""
	# Collection of metrics regarding the status of an Abstract Procedure.

	# [ Properties ]
	# /work/
		# Procedure Work Unit progress.
	# /msg/
		# Procedure message counters.
	# /usage/
		# Procedure resource usage.
	"""

	work: Work
	msg: Advisory
	usage: Resource

	def __iter__(self):
		for x in [
			('work', self.work),
			('msg', self.msg),
			('usage', self.usage),
		]:
			if x is not None:
				yield x

	@classmethod
	def create(Class):
		"""
		# Create an empty Procedure.
		"""
		return Class(Work(), Advisory(), Resource())

	def __getitem__(self, path):
		selection = self

		try:
			for a in path:
				selection = getattr(selection, a)
		except AttributeError:
			raise IndexError('.'.join(path))
		else:
			return selection

	def __add__(self, operand):
		return self.__class__(
			self.work + operand.work if self.work is not None else operand.work,
			self.msg + operand.msg if self.msg is not None else operand.msg,
			self.usage + operand.usage if self.usage is not None else operand.usage,
		)

	_metrics_symbols = {
		'%': ('work', Work),
		'@': ('msg', Advisory),
		'$': ('usage', Resource),
	}

	@classmethod
	def structure(Class, text:str):
		"""
		# Structure progress text into a &Metrics instance.
		"""

		fields = {'work': Work(), 'usage': Resource(), 'msg': Advisory()}
		for x in text.split():
			if x[:1] in Class._metrics_symbols:
				group, typ = Class._metrics_symbols[x[:1]]
				fields[group] = typ.split(x[1:])

		return Class(**fields)

	def sequence(self) -> str:
		"""
		# Return the components making up the serialized string.
		"""
		s = []

		for c in '%@$':
			field = self._metrics_symbols[c][0]
			attrv = getattr(self, field, None)
			if attrv is not None and not attrv.empty():
				s.append(c+str(attrv))

		return ' '.join(s)

def allocate_line_buffer(fd, encoding='utf-8'):
	return io.TextIOWrapper(io.BufferedReader(io.FileIO(fd, mode='r'), 2048), encoding)

def spawnframes(invocation,
		exceptions=sys.stderr,
		stdin=sys.stdin.fileno(),
		stderr=sys.stderr.fileno(),
		readsize=1024*4,
	):
	"""
	# Generator emitting frames produced by the given invocation's standard out.
	# If &GeneratorExit or &KeyboardInterrupt is thrown, the generator will send
	# the process a &signal.SIGKILL.
	"""
	interrupted = False

	rfd, wfd = os.pipe()
	pid = invocation.spawn(fdmap=[(stdin,0), (wfd,1), (stderr,2)])

	try:
		os.close(wfd)

		framesrc = allocate_line_buffer(rfd)
		with framesrc:
			lines = [framesrc.readline()] # Protocol message.
			while lines:
				frameset = []
				for line in lines:
					try:
						frameset.append(frames.structure(line))
					except:
						# Any exception means it's not a well formed frame.
						# In such cases, relay the original line to standard error.
						exceptions.write('> ' + line)
					finally:
						pass
				yield frameset
				lines = framesrc.readlines(readsize)
	except (GeneratorExit, KeyboardInterrupt) as exc:
		interrupted = True
		try:
			os.killpg(pid, signal.SIGKILL)
		except ProcessLookupError:
			pass

		raise exc
	finally:
		procx = execution.reap(pid, options=0)
		if not interrupted and procx.status != 0:
			exceptions.write("[!# WARNING: status frame source exited with non-zero result]\n")

class FrameArray(object):
	"""
	# IO array manager for frame sources.
	"""

	@tools.cachedproperty
	def io(self):
		from ..system.io import Array, alloc_input
		return (Array, alloc_input)

	def __init__(self,
		readframe=frames.structure,
		encoding='utf-8', newline=b'\n', timeout=145
	):
		self.timeout = timeout
		self.newline = newline
		self.encoding = encoding
		self._unpack = readframe
		self._ioa = None
		self._linebuffers = {}

	def __enter__(self):
		if self._ioa is None:
			self._ioa = self.io[0]()

	def __exit__(self, exc, val, tb):
		self._ioa.void()

	def connect(self, id, fd):
		channel = self.io[1](fd)
		channel.link = id
		self._ioa.acquire(channel)
		channel.acquire(bytearray(1024*8))
		self._linebuffers[id] = bytearray()

	def force(self):
		self._ioa.force()

	def frame(self, line):
		"""
		# Decode and unpack the binary status frame using Array's configuration.
		"""
		try:
			return self._unpack(line.decode(self.encoding, errors='surrogateescape'))
		except Exception as err:
			import traceback
			traceback.print_exception(err.__class__, err, err.__traceback__)

	def collect(self):
		with self._ioa.wait(self.timeout):
			return [
				# Default None transfers to b'' as the epoll implementation,
				# currently, may terminate without a corresponding read.
				(channel.link, channel.transfer() or b'', channel.terminated, channel)
				for channel in self._ioa.transfer()
			]

	def __iter__(self):
		unpack = self._unpack

		for rid, data, term, channel in self.collect():
			frameset = []
			buffer = self._linebuffers[rid]
			buffer += data

			if buffer:
				lines = buffer.splitlines(keepends=True)
				if buffer.endswith(self.newline):
					self._linebuffers[rid] = bytearray()
				else:
					# Maintain buffer.
					self._linebuffers[rid] = lines[-1]
					del lines[-1:]

				# Emit empty to signal that some buffer change occurred.
				frameset.extend(map(self.frame, lines))

			del buffer

			if term:
				# Finish buffer.
				buffer = self._linebuffers.pop(rid)
				if buffer:
					# Force newline.
					if not buffer.endswith(self.newline):
						buffer += self.newline

					lines = buffer.splitlines(keepends=True)
					frameset.extend(map(self.frame, lines))

				yield (rid, frameset)
				yield (rid, None)
			elif channel.exhausted:
				# Only reads.
				channel.acquire(bytearray(1028*8))
				yield (rid, frameset)
			else:
				yield (rid, frameset)

class Log(object):
	"""
	# Status frame serialization interface and write buffer.
	"""

	#* REFACTOR: Parameterize theme so host/user specific overrides may be employed.
	highlights = {
		'reset': '\x1b[0m',
		'error': '\x1b[31m',
		'warning': '\x1b[33m',
		'notice': '\x1b[34m',
		'synopsis': '\x1b[38;5;247m',
	}

	@staticmethod
	def _xid(extension, xid):
		if xid:
			if extension is None:
				extension = {}
			extension['@transaction'] = xid.split('\n')

		return extension

	@classmethod
	def stdout(Class, channel=None, encoding=None):
		"""
		# Construct a &Log instance for serializing frames to &sys.stdout.
		"""
		from sys import stdout
		return Class(frames.sequence, stdout.buffer, encoding or stdout.encoding, channel=channel)

	@classmethod
	def stderr(Class, channel=None, encoding=None):
		"""
		# Construct a &Log instance for serializing frames to &sys.stderr.
		"""
		from sys import stderr
		return Class(frames.sequence, stderr.buffer, encoding or stderr.encoding, channel=channel)

	def __init__(self, pack, stream, encoding, frequency=8, channel=None):
		self.channel = channel
		self.encoding = encoding
		self.frequency = frequency
		self.stream = stream
		self._pack = pack
		self._send = stream.write
		self._flush = stream.flush
		self._count = 0

	def transaction(self) -> bool:
		"""
		# Increment the operation count and check if it exceeds the frequency.
		# If in excess, flush the buffer causing serialized messages to be written
		# to the configured stream.

		# Return &True when a &flush is performed, otherwise &False.
		"""
		self._count += 1
		if self._count >= self.frequency:
			self.flush()
			return True
		return False

	def flush(self):
		"""
		# Write any emitted messages to the configured stream and reset the operation count.
		"""
		self._count = 0
		self._flush()

	def emit(self, frame):
		"""
		# Send a &message using the given &channel identifier.
		"""
		return self._send(self._pack(frame, channel=self.channel).encode(self.encoding))

	def inject(self, data:bytes):
		"""
		# Write bytes directly to the log's stream.
		"""
		self._send(data)
		self._count += 1

	def write(self, text:str):
		"""
		# Write text to the log's stream incrementing the transmit count.
		"""
		self._send(text.encode(self.encoding, errors='surrogateescape'))
		self._count += 1

	def declare(self, datum='2000-01-02', timestamp=0):
		"""
		# Emit a protocol declaration.
		"""
		ext = {
			'@timestamp': [str(timestamp)],
			'@clock': ['metric-seconds -9 ' + datum],
		}
		self.emit(frames.declaration())

	def compose(self, type, severity, qualifier, text, extension,
			channel=None,
			_compose=frames.compose
		):
		sy = self.highlights['synopsis']
		re = self.highlights['reset']
		syn = ''.join([
			self.highlights[severity],
			qualifier, re,
			sy, ': ', text[0]
		])

		hi = itertools.cycle((re, sy))
		for seg, hi in zip(text[1:], hi):
			if seg:
				syn += hi + seg

		if len(text) % 2 == 1:
			syn += re

		if channel is None:
			channel = self.channel

		return _compose(type, syn, channel, extension or {})

	def notice(self, *text, extension=None, xid=None, label='NOTICE'):
		extension = self._xid(extension, xid)
		msg = self.compose('!#', 'notice', label, text, extension)
		self.emit(msg)
		return msg

	def warning(self, *text, extension=None, xid=None, label='WARNING'):
		extension = self._xid(extension, xid)
		msg = self.compose('!#', 'warning', label, text, extension)
		self.emit(msg)
		return msg

	def error(self, *text, extension=None, xid=None, label='ERROR'):
		extension = self._xid(extension, xid)
		msg = self.compose('!#', 'error', label, text, extension)
		self.emit(msg)
		return msg

	def xact_open(self, xid, synopsis, extension):
		extension = self._xid(extension, xid)
		f = frames.compose("->", synopsis, self.channel, extension)
		self.emit(f)
		return f

	def xact_status(self, xid, synopsis, extension):
		extension = self._xid(extension, xid)
		f = frames.compose('--', synopsis, self.channel, extension)
		self.emit(f)
		return f

	def xact_close(self, xid, synopsis, extension):
		extension = self._xid(extension, xid)
		f = frames.compose("<-", synopsis, self.channel, extension)
		self.emit(f)
		return f

def _launch(status, stderr=2, stdin=0):
	# Get the next invocation from the iterator and spawn it.
	try:
		category, dimensions, xcontext, ki = next(status['process-queue'])
		status['category'] = category
		status['identifier'] = xcontext
	except StopIteration:
		return None

	rfd, wfd = os.pipe()
	try:
		status['pid'] = ki.spawn(fdmap=[(0,0), (wfd,1), (2,2)])
	except:
		os.close(rfd)
		raise
	finally:
		os.close(wfd)

	return (rfd, category, dimensions)

def _field(key, ext, default=None):
	# Retrieve the field value or default if not present or is an empty string.
	if key in ext:
		return ext[key][0] or default
	else:
		return default

def _closed(failed, start, stop, xframes, extension, /,
		executed='<>', failure='><',
		ts=tools.partial(_field, '@timestamp'),
	):
	"""
	# Join a start and stop frame.
	"""
	ext = extension
	ext.update(start.f_extension)
	ext.update(stop.f_extension)

	# Set duration from start and stop timestamps.
	if '@duration' not in ext:
		start_time = int(ts(start.f_extension, 0))
		stop_time = int(ts(stop.f_extension, 0))
		ext['@duration'] = [str(-(stop_time - start_time))]

	# Frame sources should provide non-zero metrics on both sides.
	metrics = start.f_extension.get('@metrics', []) + stop.f_extension.get('@metrics', [])
	metrics = [x for x in metrics if x.strip()]
	if metrics:
		ext['@metrics'] = metrics

	if '@frames' in ext and not ext['@frames']:
		del ext['@frames']

	# If failure is indicated, the failed transaction type should be preferred.
	if failed:
		typ = failure
	else:
		# Executed or Granted. Use the designated type if any.
		typ = ext.pop('@frame-type', [executed])[0]

	return frames.compose(typ, stop.f_image, stop.f_channel, ext)

def _open_frame(status, fcompose=frames.compose):
	ctx = status['category']
	ts = time.utc().select('iso')

	ext = {
		'@timestamp': [str(time.elapsed())],
	}
	if status['identifier']:
		ctx = status['identifier']
		ext['@transaction'] = [ctx]

	return fcompose('->', ctx + ': ' + ts, None, ext)

def dispatch(meta, log,
		plan, monitors, summary, title, queue,
		opened=False,
		select=(lambda t,m,f: False), alerts=True,
		frequency=64,
		kill=os.killpg, range=range, next=next
	):
	"""
	# Execute system commands while displaying their status
	# according to the transaction messages they emit to standard out.
	"""

	closetypes = {
		(False, True): '<>',
		(False, False): '><',
	}

	zero = Procedure.create()

	total_messages = 0
	message_count = 0

	# Status monitors are allocated for each lane.
	available = collections.deque(range(len(monitors)))

	statusd = {}
	last = time.elapsed()
	summary.reset(last, zero)
	for m in monitors:
		m.reset(last, zero)
	mtotal = zero

	summary.title(title, '/'.join(map(str, queue.status())))
	ioa = FrameArray(timeout=frequency)
	try:
		ioa.__enter__()
		processing = True
		while processing:
			if available:
				# Open processing lanes take from queue.
				for ident in queue.take(len(available)):
					lid = available.popleft()
					iki = iter(plan(ident))

					status = statusd[lid] = {
						'source': ident,
						'process-queue': iki,
						'transactions': collections.defaultdict(list),
					}

					monitor = monitors[lid]
					monitor.reset(last, zero)

					next_channel = _launch(status)
					if next_channel is None:
						queue.finish(status['source'])
						available.append(lid)
						del statusd[lid]
						continue

					monitor.title(next_channel[1], *next_channel[2])
					ioa.connect(lid, next_channel[0])

					if opened:
						log.emit(_open_frame(status))

				if queue.terminal():
					if not statusd:
						# Queue has nothing and statusd is empty? EOF.
						processing = False
						continue
					elif available:
						# End of queue and still running.
						# Check existing jobs for further work.
						sources = list(statusd)
						for lid in sources:
							while available:
								status = dict(statusd[lid])
								next_channel = _launch(status)
								if next_channel is None:
									# continues for-loop, check next list.
									break
								else:
									# Per-channel open transactions.
									status['transactions'] = collections.defaultdict(list)
									xlid = available.popleft()
									statusd[xlid] = status
									monitor = monitors[xlid]
									monitor.reset(time.elapsed(), zero)

									monitor.title(next_channel[1], *next_channel[2])
									ioa.connect(xlid, next_channel[0])

									if opened:
										log.emit(_open_frame(status))
									log.flush()
							else:
								# No more availability, exit for-sources.
								break

			# Calculate change in time for Metrics.commit.
			next_time = time.elapsed()

			# Cycle through sources, flush when complete.
			for lid, sframes in ioa:
				monitor = monitors[lid]
				status = statusd[lid]
				xacts = status['transactions']
				srcid = status['source']

				if sframes is None:
					# Closed.
					exitcode = execution.reap(execution.wait(status['pid']))

					# Send final snapshot to log.
					ftype = closetypes.get((opened, exitcode == 0), '<-')
					xf = monitor.frame(ftype, status['identifier'])
					log.emit(xf)
					log.flush()

					next_channel = _launch(status)
					monitor.reset(next_time, zero)

					if next_channel is not None:
						ioa.connect(lid, next_channel[0])

						monitor.title(next_channel[1], *next_channel[2])
						if opened:
							log.emit(_open_frame(status))
						continue

					queue.finish(status['source'])
					del statusd[lid]
					available.append(lid)

					qs = queue.status()
					summary.title(title, '/'.join(map(str, (qs[0]-len(statusd), qs[1]))))
					status.clear()
					continue

				nframes = len(sframes)
				message_count += nframes

				pdelta = zero
				for f in sframes:
					channel = f.f_channel
					evtype = f.f_event.symbol
					ext = f.f_extension or {}
					xid = (channel, tuple(ext.get('@transaction', ())))

					# Update the monitors view.
					delta = zero
					for x in ext.get('@metrics', ()):
						delta += Procedure.structure(x)
					pdelta += delta

					if evtype == 'transaction-started':
						start_frame = f
						xframes = list()
						xacts[xid] = (f, xframes)
						rf = start_frame
						failure = None
					elif evtype == 'transaction-stopped':
						start_frame, xframes = xacts.pop(xid, (None, ()))
						failure = (delta.work.w_failed > 0)
						rf = _closed(failure, start_frame, f, xframes, {})
					else:
						start_frame, xframes = xacts.get(xid, (None, ()))
						rf = f
						failure = (evtype == 'transaction-failed')

					# Report the combined frame to log if selected.
					if select(None, delta, rf):
						log.emit(rf)
						log.flush()

					# Report the failures to meta if alerts are enabled.
					if failure and alerts:
						meta.emit(rf)
						fi = rf.f_extension.get('@failure-image', ())
						if len(fi) > 1:
							fi = iter(fi); next(fi)
							op = rf.f_extension.get('@operation', ())
							if op:
								meta.write('\n'.join(op))
								meta.write('\n')
							meta.write('\n'.join(fi))
							meta.write('\n')
						meta.flush()
					# Frame Processing
				mtotal += pdelta
				monitor.update(next_time, monitor.current + pdelta)

			last = next_time

			# Update duration and any other altered fields.
			for vlid, m in enumerate(monitors):
				m.elapse(next_time)

			summary.update(next_time, mtotal)
			qs = queue.status()
			summary.title(title, '/'.join(map(str, (qs[0]-len(statusd), qs[1]))))
		else:
			pass
	except BrokenPipeError:
		pass
	finally:
		ioa.__exit__(None, None, None) # Exception has the same effect.
		for lid in statusd:
			try:
				kill(statusd[lid]['pid'], signal.SIGKILL)
			except (KeyError, ProcessLookupError):
				pass
			else:
				exit_status = execution.reap(execution.wait(status['pid']))

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

def duration_repr(seconds) -> tuple[float, str]:
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
	def r_transparent(value:Sequence[Formatter]):
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

	def style(self, celltexts:Sequence[Formatter]):
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
