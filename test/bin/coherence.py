"""
# Test the coherence of the specified project.
"""
import os
import sys
import contextlib
import signal
import functools
import types
import importlib

from ...system import corefile
from ...system import process
from ...system import files

from .. import engine

def color(color, text):
	return text

def color_identity(identity):
	parts = identity.split('.')
	parts[0] = color('0x1c1c1c', parts[0])
	parts[:-1] = [color('gray', x) for x in parts[:-1]]
	return color('red', '.').join(parts)

open_fate_message = color('0x1c1c1c', '|')
close_fate_message = color('0x1c1c1c', '|')
top_fate_messages = color('0x1c1c1c', '+' + ('-' * 10) + '+--')
working_fate_messages = color('0x1c1c1c', '|' + (' execute  ') + '|')
bottom_fate_messages = color('0x1c1c1c', '+' + ('-' * 10) + '+--')
report_core_message = '\r{start} {fate!s} {stop} {tid}                \n'

class Harness(engine.Harness):
	"""
	# The collection and execution of a series of tests.
	"""
	concurrently = staticmethod(process.concurrently)

	def _status_test_sealing(self, test):
		self.status.write('{working} {tid} ...'.format(
			working = working_fate_messages,
			tid = color_identity(test.identifier),
		))
		self.status.flush() # need to see the test being ran right now

	def _report_core(self, test):
		self.status.write(report_core_message.format(
			fate = color(test.fate.color, 'core'.ljust(8)),
			tid = color_identity(test.identifier),
			start = open_fate_message,
			stop = close_fate_message
		))

	def _handle_core(self, corefile):
		if corefile is None:
			return

		if os.path.exists(corefile):
			self.status.write("CORE: Identified, {0!r}, loading debugger.\n".format(corefile))
			from ...factors import backtrace
			debugger = backtrace.debug(corefile)
			debugger.wait()
			self.status.write("CORE: Removed file.\n".format(corefile))
			os.remove(corefile)
		else:
			self.status.write("CORE: File does not exist: " + repr(corefile) + '\n')

	def _print_tb(self, fate):
		import traceback
		tb = traceback.format_exception(fate.__class__, fate, fate.__traceback__)
		tb = ''.join(tb)
		sys.stderr.write(tb)

	def dispatch(self, test):
		faten = None
		self._status_test_sealing(test)

		# seal fate in a child process
		def manage():
			nonlocal self
			nonlocal test
			with test.exits:
				self.seal(test)
		seal = self.concurrently(manage)

		l = []
		report = seal(status_ref = l.append)

		if report is None:
			report = {'fate': 'unknown', 'impact': -1, 'interrupt': None}

		pid, status = l[0]

		if os.WCOREDUMP(status):
			faten = 'core'
			report['fate'] = 'core'
			test.fate = self.Core(None)
			self._report_core(test)
			self._handle_core(corefile.location(pid))
		elif not os.WIFEXITED(status):
			# redrum
			import signal
			try:
				os.kill(pid, signal.SIGKILL)
			except OSError:
				pass

		report['exitstatus'] = os.WEXITSTATUS(status)

		if False and report['impact'] < 0 or report['interrupt']:
			sys.exit(report['exitstatus'])

		return report

	def seal(self, test):
		sys.stderr.write('\b\b\b' + str(os.getpid()))
		sys.stderr.flush() # want to see the test being ran

		try:
			signal.signal(signal.SIGALRM, test.timeout)
			signal.alarm(8)

			test.seal()
		finally:
			signal.alarm(0)
			signal.signal(signal.SIGALRM, signal.SIG_IGN)

		faten = test.fate.subtype
		parts = test.identifier.split('.')
		parts[0] = color('0x1c1c1c', parts[0])
		if test.fate.impact >= 0:
			parts[1:] = [color('gray', x) for x in parts[1:]]
		else:
			parts[1:-1] = [color('gray', x) for x in parts[1:-1]]

		ident = color('red', '.').join(parts)
		sys.stderr.write('\r{start} {fate!s} {stop} {tid}                \n'.format(
			fate = color(test.fate.color, faten.ljust(8)),
			tid = ident,
			start = open_fate_message,
			stop = close_fate_message
		))

		report = {
			'test': test.identifier,
			'impact': test.fate.impact,
			'fate': faten,
			'interrupt': None,
		}

		if test.fate.subtype == 'divide':
			ident = '/'.join((self.identity, test.identifier))
			subharness = self.__class__(ident, test.subject, test.fate.content)
			subharness.reveal()
		elif test.fate.impact < 0:
			if isinstance(test.fate.__cause__, KeyboardInterrupt):
				report['interrupt'] = True
			self._print_tb(test.fate)
			import pdb
			# error cases chain the exception
			if test.fate.__cause__ is not None:
				tb = test.fate.__cause__.__traceback__
			else:
				tb = None
			if tb is None:
				tb = test.fate.__traceback__
			pdb.post_mortem(tb)

	def reveal(self):
		self.status.write(top_fate_messages + '\n')
		super().reveal()
		self.status.write(bottom_fate_messages + '\n')

def main(inv:process.Invocation) -> process.Exit:
	module_path, *testslices = inv.args # Import target and start[:stop] tests.
	slices = []
	for s in testslices:
		if ':' in s:
			start, stop = s.split(':')
		else:
			start = s
			stop = ''
		slices.append((start or None, stop or None))

	p = Harness.from_module(importlib.import_module(module_path), slices=slices)
	p.status = sys.stderr
	p.reveal()
	return inv.exit(0)

if __name__ == '__main__':
	with corefile.constraint(None):
		process.control(main, process.Invocation.system())
