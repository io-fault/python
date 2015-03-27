"""
Lower-level interfaces to managing queues, processes, processing threads, and memory.

libhazmat is, in part, fork's :py:mod:`threading` implementation along with
other primitives and tools used by forking processes. However, its structure is vastly
different from :py:mod:`threading` as the class structure is unnecessary for libhazmat's
relatively lower-lever applications. The primitives provided mirror many of the
:py:mod:`_thread` library's functions with minimal or no differences.

The memory management interfaces exist to support a memory pool for applications
that need to enforce limits in particular areas. Python's weak references are used
to allow simple chunk reclaims when all the references are destroyed.

The process management interfaces exist to abstract the operating system's.

The queue managemnent interfaces provide queue implementations and containment tools for
interleaving processing chains for cooperative areas of an application.
"""
import os
import sys
import collections
import functools
import operator
import signal
import weakref
import _thread

from . import system

processing_structure = ('kernel', 'group', 'process', 'thread',)
memory_structure = ('bytes',)

##
# Threading Primitives.
##

#: Mutex. Acquire a low-level lock primitive used for the synchronization of threads.
create_knot = _thread.allocate_lock

#: Return the low-level identity of the thread.
identify_thread = _thread.get_ident

#: Create a new thread.
create_thread = _thread.start_new_thread

#: Get the frame of a particular thread.
select_thread = lambda x: sys._current_frames().get(x)

#: Get the frames of a set of threads.
def select_fabric(tids):
	snapshot = sys._current_frames()
	r = [
		(x, snapshot[x]) for x in tids
	]
	return r

class Sever(BaseException):
	"""
	Exception used to signal thread kills.
	"""
	__kill__ = True

#: Kill a thread at the *Python* level.
def cut_thread(tid, exception = Sever, setexc = system.interrupt):
	"""
	interrupt(thread_id, exception = Sever)

	Raise the given exception in the thread with the given identifier.

	.. warning:: Cases where usage is appropriate is rare.
	"""
	r =  setexc(tid, exc)
	signal.pthread_kill(tid, signal.SIGINT)
	return r

def pull_thread(callable, *args):
	"""
	:returns: Reference to the :py:class:`Contained` result.
	:rtype: Callable

	Execute a callable in a new thread returning a (callable) reference to
	the contained result. When the returned object is called, a mutex will
	be used in order to synchronize access to the result.

	pull_thread is best used in situations where concurrent processing should
	occur while waiting on another result, ideally a system call that will
	allow the dispatching-thread to run.

	In :py:mod:`threading` terms, this is equivalent to creating and running a new thread
	and joining it back into calling thread.
	"""
	t = Transition()
	create_thread(t.relay, callable, *args)
	return t.commit

##
# Process Related mappings
##

#: Normalized identities for signals.
process_signals = {
	'stop': signal.SIGSTOP,
	'istop': signal.SIGTSTP,
	'continue': signal.SIGCONT,
	'terminate' : signal.SIGTERM,
	'quit' : signal.SIGQUIT,
	'interrupt' : signal.SIGINT,
	'kill' : signal.SIGKILL,

	'terminal.query': getattr(signal, 'SIGINFO', None),
	'terminal.view': getattr(signal, 'SIGWINCH', None),

	'delta': signal.SIGHUP,
	'context': signal.SIGUSR1,
	'trip' : signal.SIGUSR2,

	'limit-cpu': signal.SIGXCPU,
	'limit-file.size': signal.SIGXFSZ,
	'profiler': signal.SIGPROF,
}

#: Signal numeric identifier to Signal Names mapping.
process_signal_names = dict([(v, k) for k, v in process_signals.items()])

#: Signals that *would* terminate the process *if* SIG_DFL was set.
process_fatal_signals = {
	signal.SIGINT,
	signal.SIGTERM,
	getattr(signal, 'SIGXCPU', None),
	getattr(signal, 'SIGXFSZ', None),
	getattr(signal, 'SIGVTALRM', None),
	getattr(signal, 'SIGPROF', None),
	getattr(signal, 'SIGUSR1', None),
	getattr(signal, 'SIGUSR2', None),
}
process_fatal_signals.discard(None)

process_signal_identifiers = {
	getattr(signal, name): name
	for name in dir(signal)
	if name.startswith('SIG') and name[3] != '_' and isinstance(getattr(signal, name), int)
}

def process_delta(
	pid,
	wasexit = os.WIFEXITED,
	getstatus = os.WEXITSTATUS,

	wassignal = os.WIFSIGNALED,
	getsig = os.WTERMSIG,

	wasstopped = os.WIFSTOPPED,
	getstop = os.WSTOPSIG,

	wascontinued = os.WIFCONTINUED,

	wascore = os.WCOREDUMP,

	waitpid = os.waitpid,
	options = os.WNOHANG | os.WUNTRACED,
):
	"""
	process_delta(pid)

	:param pid: The process identifier to reap.
	:type pid: :py:class:`int`
	:returns: (pid, event, status, core)
	:rtype: tuple or None

	The event is one of: 'exit', 'signal', 'stop', 'continue'.
	The first two mean that the process has been reaped and their `core` field will be
	:py:obj:`True` or :py:obj:`False` indicating whether or not the process left a coredump
	behind. If the `core` field is :py:obj:`None`, it's an authoritative statement that
	the process did not exit.

	The status code is the exit status if an exit event, the signal number that killed or
	stopped the process, or None in the case of continue.
	"""
	try:
		_, code = waitpid(pid, options)
	except OSError:
		return None

	if wasexit(code):
		event = 'exit'
		status = getstatus(code)
		cored = wascore(code) or False
	elif wassignal(code):
		event = 'signal'
		status = - getsig(code) or 0
		cored = wascore(code) or False
	elif wasstopped(code):
		event = 'stop'
		status = getstop(code) or 0
		cored = None
	elif wascontinued(code):
		event = 'continue'
		status = None
		cored = None

	return (event, status, cored)

class ContainerException(Exception):
	"""
	Common containment Exception.
	"""

class Containment(ContainerException):
	"""
	Raised when an open call attempts to access a contained exception.

	:py:attr:`__cause__` contains the original, contained, exception.
	"""

class ContainerError(ContainerException):
	'Base class for **errors** involving containers'
class VoidError(ContainerError):
	'Raised when access to an absent resource occurs.'
class NoExceptionError(VoidError):
	'Raised when a Return is contained, but the Exception was accessed.'
class NoReturnError(VoidError):
	'Raised when an Exception is contained, but the Return was accessed.'

##
# Python Callable Result Containers
##

class Container(tuple):
	"""
	An object that contains either the returned object or the raised exception.
	"""
	#: Whether or not the Contained object was raised.
	__slots__ = ()
	failed = None
	contained = property(operator.itemgetter(0), doc = 'The contained object.')

	_fields = ('contained',)
	@property
	def __dict__(self, OrderedDict = collections.OrderedDict, _fields = _fields):
		return OrderedDict(zip(_fields, self))

	def self(self):
		"""
		Return the container itself; useful for cases where a reference is needed.
		"""
		return self

	def shed(self):
		"""
		Given an object contained within a container, return the innermost
		*Container*.
		"""
		c = self
		while isinstance(c.contained, Container):
			c = c.contained
		return c

	def open(self):
		"""
		Open the container with the effect that the original Contained callable
		would have. If the contained object was raised as an exception, raise the
		exception. If the contained object the object returned by the callable,
		return the contained object.
		"""
		raise VoidError(self)
	__call__ = open

	def inject(self, generator):
		"""
		Given an object supporting the generator interface, `throw` or `send` the
		contained object based on the Container's
		:py:attr:`Container.failed` attribute.
		"""
		raise VoidError()

	def exception(self):
		"""
		Open the container returning the exception raised by the Contained
		callable.

		An exception, :py:class:`.VoidError`, is raised iff the
		Contained object is not an exception-result.
		"""
		raise VoidError()

	def returned(self):
		"""
		Open the container returning the object returned by the Contained
		callable.

		An exception, :py:class:`.VoidError`, is raised iff the
		Contained object is not a return-result.
		"""
		raise VoidError()

	def endpoint(self, callback):
		"""
		Give the container to the callback.

		This method exists explicitly to provide interface consistency with Deliveries.
		Rather than conditionally checking what was returned by a given function that
		may be deferring subsequent processing, a container can be returned and immediately
		passed to the next call.
		"""
		return callback(self)

class ContainedReturn(Container):
	"""
	The Container type a return-result.

	See :py:class:`Container` for details.
	"""
	__slots__ = ()
	failed = False

	def open(self):
		return self[0]
	returned = open
	__call__ = open

	def exception(self):
		raise NoExceptionError(self)

	def inject(self, generator):
		return generator.send(self[0])

class ContainedRaise(Container):
	"""
	The Container type for an exception-result.

	See :py:class:`Container` for details.
	"""
	__slots__ = ()
	failed = True

	def _prepare(self):
		contained_exception, traceback, why = self
		contained_exception.__traceback__ = traceback
		contained_exception.__cause__, contained_exception.__context__ = why
		contained = Containment()
		contained.container = self
		contained.__cause__ = contained_exception
		return (contained, contained_exception)

	def open(self):
		containment, contained_exception = self._prepare()
		raise containment from contained_exception # opened a contained raise
	__call__ = open

	def returned(self):
		raise NoReturnError(self.contained)

	def exception(self):
		return self[0]

	def inject(self, generator):
		contained, contained_exception = self._prepare()
		self.__class__ = Container
		generator.throw(Contained, contained, None)

def contain(callable, *args,
	ContainedReturn = ContainedReturn,
	ContainedRaise = ContainedRaise,
	BaseException = BaseException,
	getattr = getattr
):
	"""
	contain(callable, *args)

	:param callable: The object to call with the given arguments.
	:type callable: :py:class:`collections.Callable`
	:param args: The positional arguments to pass on to `callable`.
	:returns: The Contained result.

	Construct and return a Container suitable for the fate of the given
	callable executed with the given arguments.

	The given callable is only provided with positional parameters. In cases
	where keywords need to be given, :py:class:`functools.partial` should be used prior to
	calling `contain`.
	"""
	try:
		return ContainedReturn((callable(*args),None,None)) ### Exception was Contained ###
	except BaseException as exc:
		# *All* exceptions are trapped here, save kills.
		if getattr(exc, '__kill__', None) is True:
			raise
		return ContainedRaise((exc,exc.__traceback__,(exc.__cause__,exc.__context__)))

def chain(iterable, initial, contain = contain):
	"""
	chain(iterable, initial)

	:param iterable: The generators to connect.
	:type iterable: :py:class:`collections.Iterable`
	:param initial: The initial Container to give to the first generator.
	:type initial: :py:class:`Container`

	Given an iterable of generators, send or throw the Contained result into the
	next, returning the last container result.

	In the case of a ContainedRaise, throw the actual exception into the
	generator, not Containment. Chain discard the Container leaving
	little possibility of another open mangling the traceback.

	.. note:: The `initial` container given should not be used again.
	"""
	param = initial
	for generator in iterable:
		why = param[0]
		if param.failed:
			param = contain(generator.throw, why.__class__, why, why.__traceback__)
		else:
			param = contain(generator.send, why)
	return param

class Delivery(object):
	"""
	A reference to the delivery of a Container.

	Delivery objects allow for latent assignments of the "container" to be
	delivered and the latent "endpoint" that it is to be delivered to.
	Latent being defined at an arbitrary time in the future.

	Delivery should be used in cases where completion of an operation
	depends on a subsequent event. The event is received by an object
	controlled or known by the called function, but not the caller.

	.. note:: Connecting deliveries with Joins is a powerful combination.
	"""
	__slots__ = ('callback', 'container')

	def __init__(self):
		self.callback = None
		self.container = None

	def send(self, container):
		"""
		Deliver the given arguments to the designated endpoint.
		If there is no endpoint, hold onto the arguments until a corresponding
		:py:meth:`endpoint` call is performed allowing
		delivery to be committed.
		"""
		self.container = container
		if self.callback is not None:
			self.commit()

	def endpoint(self, callback):
		"""
		Specify the given `callback` as the designated endpoint.
		If there is no package, hold onto the `callback` until a corresponding
		:py:meth:`send` call is performed allowing
		delivery to be committed.
		"""
		self.callback = callback
		if self.container is not None:
			self.commit()

	def commit(self):
		return self.callback(self.container)

class Switch(object):
	"""
	Event driven mutex.

	A queue that manages callbacks that are invoked when a given
	callback reached the head of the queue.

	Using :py:class:`nucleus.libhazmat.create_knot` in combination with join
	is a great way to manage continuations based on exclusive access.

	.. warning:: Do not use.
	"""
	__slots__ = ('_current', '_waiters',)

	def __init__(self, Queue = collections.deque):
		self._waiters = Queue()
		self._current = None

	def acquire(self, callback):
		"""
		:returns: Whether or not it was **immediately** acquired.
		:rtype: :py:class:`bool`
		"""
		self._waiters.append(callback)
		# At this point, if there is a _current,
		# it's release()'s job to notify the next
		# owner.
		if self._current is None and self._waiters[0] is callback:
			self._current = self._waiters[0]
			self._current()
			return True
		return False

	def release(self):
		"""
		:returns: Whether or not the Switch was released **to another controller**.
		:rtype: :py:class:`bool`
		"""
		if self._current is not None:
			if not self._waiters:
				# not locked
				return False
			self._waiters.popleft()

			if self._waiters:
				# new owner
				self._current = self._waiters[0]
				self._current()
			else:
				self._current = None
		return True

	def locked(self):
		return self._current is not None

class Transition(object):
	"""
	A synchronization mechanism used to manage the transition
	of an arbitrary Container from one thread to another.

	Transitions are used by two threads in order to synchronize
	a single transfer.

	In terms of Python's threading library, Transitions would
	be the kind of synchronization mechanism used to implement
	:py:meth:`threading.Thread.join`
	"""
	__slots__ = ('mutex', 'container')

	def __init__(self, mutex = create_knot):
		self.container = None
		# acquire prior to setting
		mtx = mutex()
		mtx.acquire()
		self.mutex = mtx

	def commit(self):
		"""
		Commit to the transition. If the object
		hasn't been placed, block until it is.

		A RuntimeError will be raised upon multiple invocations of commit.
		"""
		mutex = self.mutex
		if mutex is None:
			raise RuntimeError("transitioned")
		with mutex:
			self.mutex = None
			return self.container.open() # Thread Result

	def endpoint(self, container):
		"""
		Initiate the transition using the given container.
		"""
		mutex = self.mutex
		if mutex is None:
			raise RuntimeError("transitioned")
		self.container = container
		mutex.release()

	def relay(self, callable, *args, contain = contain):
		return self.endpoint(contain(callable, *args))

class EQueue(object):
	"""
	An event driven queue where references to readers and references
	to writers are passed in order to conflate queue event types.

	This implementation is *not* thread safe.

	Event driven queues have a remarkable capability of providing a
	means to communicate when the reader of the queue wants more.
	By using "NULL" items, a the source of items can identify that
	the receptor is looking to retrieve more information.

	.. warning:: get and put operations are **not** thread safe.
	"""
	__slots__ = ('state', 'struct')

	def __init__(self, storage = None, Queue = collections.deque):
		# writers are appended right of the "center"
		# readers are prepended left of the "center"
		self.struct = Queue(storage) if storage is not None else Queue()

		# negative means waiting readers
		# positive means waiting writers
		self.state = len(self.struct)

	@property
	def backlog(self):
		return self.state

	def send(self, container):
		return self.put(container.self)

	def put(self, item):
		if self.state >= 0:
			self.state += 1
			self.struct.append(item)
		else:
			# have readers; they appendleft of zero
			target = self.struct.pop()
			self.state += 1
			target(item)
			return True
		return False

	def endpoint(self, callback):
		if callback is None:
			return
		if self.state <= 0:
			self.state -= 1
			self.struct.appendleft(callback)
		else:
			# have writers; they appendright of zero
			item = self.struct.popleft()
			self.state -= 1
			callback(item)
			return True
		return False
	get = endpoint

	def fasten(self, src):
		"""
		Fasten two :py:class:`Queue` instances together sending items from
		the source to the destination.

		.. warning:: Currently, there is no way to terminate a connection.

		Often, if possible, it is better to replace the destination queue with
		the source. This provides the desired functionality without the extra
		effort.
		"""
		def didget(x, dop = self.put, sop = src.get):
			dop(x)
			sop(didget) # enqueue the next transfer
		src.get(didget)

class XQueue(EQueue):
	"""
	Unbounded Blocking Queue for interthread communication.

	Puts do not wait. Similar to a barrier, but gets do when
	there are no items.
	"""
	__slots__ = EQueue.__slots__ + ('mutex',)

	def __init__(self, Mutex = create_knot):
		super().__init__()
		self.mutex = Mutex()

	def get(self):
		with self.mutex:
			if self.state > 0:
				# no waiting mode; no transition needed
				self.state -= 1
				return self.struct.popleft()
			# enqueue a transition callback
			T = Transition()
			super().get(T.endpoint)
		return T.commit()

	def put(self, item):
		with self.mutex:
			super().put(item)

##
# Memory
##

class Memory(bytearray):
	"""
	bytearray subclass supporting weak-references and
	identifier hashing for memory-free signalling.
	"""
	try:
		import resource
		pagesize = resource.getpagesize()
		del resource
	except ImportError:
		pagesize = 1024

	__slots__ = ('__weakref__',)

	def __hash__(self, id=id):
		return id(self)

class Source(object):
	"""
	Memory Pool that uses weakref's to reclaim memory.
	"""
	Memory = Memory # bytearray subclass with weakref support
	Reference = weakref.ref # for reclaiming memory

	@classmethod
	def from_mib(typ, size):
		"""
		Construct a Reservoir from the given number of Mebibytes desired.
		"""
		pages, remainder = divmod((size * (2**20)), self.Memory.pagesize)
		if remainder:
			pages += 1
		return typ(pages)

	def __init__(self, capacity = 8, Queue = collections.deque):
		self.capacity = capacity
		self.blocksize = 2
		self.allocsize = self.blocksize * self.Memory.pagesize
		self.transfer_allocations = 3

		self.segments = Queue()
		self.requests = Queue()
		self.current = None
		self._allocated = set()
		for x in range(self.capacity):
			self.segments.append(self.Memory(self.Memory.pagesize))

	@property
	def used(self):
		"""
		Memory units currently in use.
		"""
		return len(self._allocated)

	@property
	def available(self):
		"""
		Number of memory units available.
		"""
		return len(self.segments)

	def alloc(self):
		"""
		Allocate a unit of memory for use. When Python references to the memory object
		no longer exist, the Reservoir will add another unit.
		"""
		if not self.segments:
			raise RuntimeError("empty")
		mem = self.segments.popleft()
		self._allocated.add(self.Reference(mem, self.reclaim))
		return mem

	def reclaim(self, memory, len = len):
		# Executed by the weakref() when the Memory() instance
		# is no longer referenced.

		# Remove weakreference reference.
		self._allocated.discard(memory)
		# Expand the Pool to fill in the new vacancy
		self.segments.append(self.Memory(self.Memory.pagesize))

		# signal transfer possible when in demand?
		if self.requests:
			pass

	def acquire(self, event):
		self.segments.extend(event)

	def transfer(self):
		return self.alloc()
