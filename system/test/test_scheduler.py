import os
import time
from .. import kernel as module

def test_Scheduler_close(test):
	"""
	# - &module.Scheduler.close
	# - &module.Scheduler.closed

	# Validate the effect of closing a scheduler instance.
	"""

	k = module.Scheduler()
	test/k.closed == False
	test/k.close() == True
	test/k.closed == True

	test/k.close() == False # already closed
	test/k.closed == True

	test/k.wait() == 0

	# Task still functions.
	k.enqueue((lambda: None))
	test/k.execute(None) == 1

def test_Scheduler_execute(test):
	"""
	# - &module.Scheduler.execute

	# Validate the execution of enqueued tasks.
	"""

	k = module.Scheduler()
	x = False
	def effect():
		nonlocal x
		x = True

	test/k.loaded == False
	k.enqueue(effect)
	test/k.loaded == True
	test/k.execute(None) == 1
	test/k.loaded == False
	test/x == True

	test/k.execute(None) == 0
	test/k.loaded == False

def test_Scheduler_execute_error_trap(test):
	"""
	# - &module.Scheduler.execute
	"""

	k = module.Scheduler()
	x = False
	def trap(ob, err):
		nonlocal x
		x = (ob, err)
	def effect():
		raise ValueError("data")

	k.enqueue(effect)
	test/k.execute(trap) == 1

	test/x[0] == effect
	test.isinstance(x[1], ValueError)
	test/x[1].args == ("data",)

def test_execute_nothing(test):
	"""
	# - &module.Scheduler.execute
	"""

	k = module.Scheduler()
	for x in range(512):
		test/k.loaded == False
		test/k.execute(None) == 0

def test_enqueue_interrupt(test):
	"""
	# - &module.Scheduler.execute

	# &module.Scheduler.enqueue should be sensitive to the event wait state.
	# This validates that no timeout event is generated designating that a
	# user event was received.
	"""

	k = module.Scheduler()
	k._set_waiting()
	k.enqueue((lambda: None))

	# Clear queue to allow kernelq_receive to be performed.
	test/k.execute(None) == 1
	test/k.wait(0) == 1

def test_dispatch_actuate(test):
	"""
	# - &module.Event.meta_actuate

	# Check that actuate is dispatched.
	"""

	events = []
	N = module.Event.meta_actuate(None)
	ln = module.Link(N, (lambda x: events.append(x.event)))

	ks = module.Scheduler()
	try:
		ks.dispatch(ln)
		test/ks.wait(0) == 1
		test/ks.execute(None) == 1
		test/(ln in ks.operations()) == False

		# Too late.
		lnf = module.Link(N, (lambda x: None))
		test/ValueError ^ (lambda: ks.dispatch(lnf))
	finally:
		ks.void()

	test/len(events) == 1
	test/id(events[0]) == id(ln.event)

def test_dispatch_terminate(test):
	"""
	# - &module.Event.meta_terminate

	# Check that terminate is dispatched.
	"""

	events = []
	N = module.Event.meta_terminate(None)
	ln = module.Link(N, (lambda x: events.append(x.event)))

	ks = module.Scheduler()
	try:
		ks.dispatch(ln)
		test/ks.wait(0) == 0
		test/ks.execute(None) == 0
		test/(ln in ks.operations()) == True

		test/ks.close() == True
		test/ks.execute(None) == 1
		test/(ln in ks.operations()) == False

		# Nothing more.
		test/ks.execute(None) == 0
	except:
		ks.void()

	test/len(events) == 1
	test/id(events[0]) == id(ln.event)

def test_Link_never_states(test):
	"""
	# - &module.Event.never

	# Check that never is available and has no immediate effect.
	"""

	events = []
	N = module.Event.never(None)
	ln = module.Link(N, (lambda x: events.append(1)))

	ks = module.Scheduler()
	try:
		ks.dispatch(ln)
		test/ln.dispatched == True
		test/ln.cancelled == False

		test/ks.wait(0) == 0
		test/ks.execute(None) == 0
		ks.cancel(ln)
		test/ks.wait(0) == 0
		test/ks.execute(None) == 0
	finally:
		ks.void()

	test/sum(events) == 0

def test_Link_scheduler_states(test):
	"""
	# - &module.Event.time
	"""

	events = []
	N = module.Event.time(0)
	ln = module.Link(N, (lambda x: events.append(x)))

	ks = module.Scheduler()
	try:
		test/ln.dispatched == False
		test/ln.cancelled == False

		ks.dispatch(ln, cyclic=False)
		test/ln.dispatched == True
		test/ln.cancelled == False

		test/ks.wait(1) == 1
		test/ks.execute(None) == 1

		test/ks.wait(0) == 0
		test/ks.execute(None) == 0

		test/ln.dispatched == True
		test/ln.cancelled == True
	finally:
		ks.void()

	test/len(events) == 1

def test_execute_error_trap_exceptions(test):
	"""
	# - &module.Scheduler.execute
	"""

	test.explicit()
	out = []
	def etrap(ob, err):
		out.append((ob, err))
		raise RuntimeError("exception during exception")

	k = module.Scheduler()
	k.enqueue(None)
	test/k.execute(etrap) == 1

def test_interrupt(test):
	"""
	# - &module.Scheduler.interrupt
	"""
	ki = module.Scheduler()
	try:
		a=time.time()
		ki.dispatch(module.Link(module.Event.time(second=5), (lambda x: None)))
		test/ki.interrupt() == None

		ki._set_waiting()
		test/ki.interrupt() == True
		ki.interrupt()
		# signals that it was already tripped
		test/ki.interrupt() == False
		test/ki.interrupt() == False
		# forced while not waiting outside block validate that it's not drop through.
		ki.wait()

		test/ki.interrupt() == None
		b=time.time()
		test/(b-a) < 5
	finally:
		ki.void()
		test.garbage()

def test_Event_time_units(test):
	"""
	# - &module.Event

	# Time events are distinct regardless of their timing.
	"""
	evt = module.Event.time
	test/evt() != evt(0)
	test/evt(1) != evt(nanosecond=1)

	ms = evt(millisecond=200)
	test/ms == ms
	us = evt(microsecond=200)
	test/us == us
	ns = evt(nanosecond=200)
	test/ns == ns
	s = evt(second=200)
	ns2 = evt(200)

	# All event instances.
	for i in [s, ms, us, ns, ns2]:
		test.isinstance(i, module.Event)
		test/i.type == 'time'

def test_Event_process_pid(test):
	"""
	# - &module.Event.process_exit
	"""
	allocproc = module.Event.process_exit

	# Expect argument requirement.
	test/TypeError ^ allocproc

	try:
		xev = allocproc(0)
	except OSError:
		# linux
		import os
		xev = allocproc(os.getpid())
		xev2 = allocproc(os.getpid())
		test/id(xev2) != id(xev)
		test/xev2 != xev
	else:
		test.isinstance(xev, module.Event)
		xev2 = allocproc(0)

		test/id(xev2) != id(xev)
		test/xev2 == xev
		test/allocproc(0) != allocproc(1)
		test/allocproc(1) == allocproc(1)

def test_Event_time(test):
	ki = module.Scheduler()
	try:
		ln = module.Link(module.Event.time(1), (lambda ln: None))
		ki.dispatch(ln, cyclic=False)
		test/ki.wait(1) == 1
		test/ki.wait(0) == 0
		test/ki.wait(0) == 0
		test/ki.execute(None) == 1
	finally:
		ki.void()
		test.garbage()

def test_interrupt_ignored(test):
	"""
	# Check that interrupt outside of wait has no effect.
	"""
	ki = module.Scheduler()
	ev = module.Event.time(0, millisecond=1200)
	try:
		a=time.time()
		ln = module.Link(ev, (lambda x: None))
		ki.dispatch(ln)
		ki.interrupt()
		ki.wait(2)
		b=time.time()
		test/(b-a) >= 1
	finally:
		ki.void()
		test.garbage()

def test_time_event_periodic(test):
	ki = module.Scheduler()
	events = []
	try:
		a=time.time()
		# recur about 500ms
		ln = module.Link(module.Event.time(millisecond=100), (lambda x: events.append(x)))
		ki.dispatch(ln)
		for x in range(5):
			ki.wait()
			ki.execute(None)

		b=time.time()
		# approx half a second
		test/(b-a) < 0.8

		# cancellation
		ki.cancel(ln)
		test/ki.wait(0)
		test/ki.execute(None) == 0
	finally:
		ki.void()
		test.garbage()

def test_signal_trap(test):
	"""
	# - &module.Event.process_signal

	# Validate the execution of system process exit events.
	"""
	import os
	import signal

	events = []
	ki = module.Scheduler()
	try:
		ln = module.Link(module.Event.process_signal(signal.SIGUSR2), (lambda x: events.append(x)))

		ki.dispatch(ln)
		test/ki.wait(0) == 0
		test/ki.execute(None) == 0

		os.kill(os.getpid(), signal.SIGUSR2)
		test/ki.wait(0) == 1
		test/ki.execute(None) == 1
	finally:
		ki.void()
		test.garbage()

	test/events == [ln]

def test_process_exit(test):
	"""
	# - &module.Event.process_exit

	# Validate the execution of system process exit events.
	"""
	import os
	status = pid = None
	r, w = os.pipe()
	def child(fd = r):
		i = os.read(fd, 1)
		os._exit(3)

	def subprocess_exit_cb(link):
		nonlocal pid, status
		status = os.waitpid(pid, os.P_WAIT)[1]

	ki = module.Scheduler()
	try:
		pid = os.fork()

		if pid == 0:
			child()
		else:
			ln = module.Link(module.Event.process_exit(pid), subprocess_exit_cb)
			ki.dispatch(ln)
			os.write(w, b'f')

		# Initial executing queue is empty.
		ki.wait()
		ki.execute(None)

		test/os.WIFEXITED(status) == True
		test/os.WEXITSTATUS(status) == 3
	finally:
		ki.void()
		test.garbage()

def test_Scheduler_io_pipe(test):
	"""
	# - &module.Event.io_transmit
	# - &module.Event.io_receive
	# - &module.Scheduler.wait
	# - &module.Scheduler.dispatch

	# Validate transmit and receive signals on regular pipes.
	"""
	import os
	import fcntl
	ioe = []

	r, w = os.pipe()
	for x in [r, w]:
		flags = fcntl.fcntl(x, fcntl.F_GETFL)
		fcntl.fcntl(x, fcntl.F_SETFL, flags | os.O_NONBLOCK)

	rxe = module.Event.io_receive(r, w)
	txe = module.Event.io_transmit(w, r)

	ki = module.Scheduler()
	try:
		data = b''
		rx = module.Link(rxe, lambda x: ioe.append(os.read(x.event.port, 2048)))
		tx = module.Link(txe, lambda x: os.write(x.event.port, data))
		ki.dispatch(rx)
		ki.dispatch(tx)

		data = b'first'
		ki.wait(0)
		ki.execute(None)
		# Allow receive to occur.
		data = b''
		ki.wait(0)
		ki.execute(None)

		data = b'second'
		ki.wait(0)
		ki.execute(None)
		tx()
		# Allow receive to occur.
		data = b''
		ki.wait(0)
		ki.execute(None)
	finally:
		ki.void()
		test.garbage()

	ioe = [x for x in ioe if x]
	test/ioe[0] == b'first'
	ioe[1] in test/{b'second', b'second'*2}

if __name__ == '__main__':
	import sys; from ...test import library as libtest
	libtest.execute(sys.modules[__name__])
