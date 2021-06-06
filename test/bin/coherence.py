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
from ...transcript import frames
from ...time.sysclock import elapsed
from ...status import python

from .. import engine
from .. import core

status_identifiers = {
	'skip': 'skipped',
	'return': 'passed',
	'pass': 'passed',
	'fail': 'failed',
	'core': 'failed',
	'error': 'failed',
}

def open_factor_transaction(time, factor, intention='unspecified', channel=''):
	msg = frames.types.Message.from_string_v1(
		"transaction-started[->]: " + factor,
		protocol=frames.protocol
	)
	msg.msg_parameters['data'] = frames.types.Parameters.from_pairs_v1([
		('time-offset', time),
	])

	return channel, msg

def close_factor_transaction(time, factor, channel=''):
	msg = frames.types.Message.from_string_v1(
		"transaction-stopped[<-]: " + factor,
		protocol=frames.protocol
	)
	msg.msg_parameters['data'] = frames.types.Parameters.from_pairs_v1([
		('time-offset', time),
	])

	return channel, msg

def open_test_transaction(time, identifier, pid, synopsis, channel=''):
	msg = frames.types.Message.from_string_v1(
		"transaction-started[->]: " + synopsis,
		protocol=frames.protocol
	)
	msg.msg_parameters['data'] = frames.types.Parameters.from_pairs_v1([
		('time-offset', time),
		('test', identifier),
		('process-identifier', pid),
	])

	return msg

def test_metrics_signal(time, fate, rusage):
	counts = {status_identifiers.get(fate, fate):1}
	r = frames.metrics(time, {'usage': rusage.ru_stime + rusage.ru_utime}, counts)
	msg = frames.types.Message.from_string_v1(
		"transaction-event[--]: METRICS: test process data",
		protocol=frames.protocol
	)
	msg.msg_parameters['data'] = r

	return msg

def sequence_failure(error):
	while error is not None:
		yield python.failure(error, error.__traceback__)
		error = getattr(error, '__cause__', None) or getattr(error, '__context__', None)

def close_test_transaction(time, identifier, pid, synopsis, failure, status, rusage):
	msg = frames.types.Message.from_string_v1(
		"transaction-stopped[<-]: " + synopsis,
		protocol=frames.protocol
	)
	msg.msg_parameters['data'] = frames.types.Parameters.from_pairs_v1([
		('time-offset', time),
		('identifier', identifier),
		('fate', synopsis),
		('failure', failure),
		('status', status),
		('system', rusage.ru_stime),
		('user', rusage.ru_utime),
	])

	return msg

class Harness(engine.Harness):
	"""
	# The collection and execution of a series of tests.
	"""
	concurrently = staticmethod(process.concurrently)

	def _status_test_sealing(self, test):
		pass

	def _report_core(self, test):
		pass

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
		start_time = elapsed()

		# seal fate in a child process
		def manage():
			nonlocal self
			nonlocal test
			with test.exits:
				return self.seal(test)
		pid, seal = self.concurrently(manage, waitpid=os.wait4)
		channel = self.channel + '/' + test.identifier + '/system/' + str(pid)

		l = []
		start_message = open_test_transaction(
			start_time, test.identifier, pid, 'start',
		)
		self.log.emit(channel, start_message)

		report = seal(status_ref = l.append)
		stop_time = elapsed()

		if report is None:
			report = {'fate': 'unknown', 'impact': -1, 'interrupt': None}

		pid, status, rusage = l[0]

		if os.WCOREDUMP(status):
			faten = 'core'
			report['fate'] = 'core'
			test.fate = core.Fate('process core dump', subtype='core')
			self._handle_core(corefile.location(pid))
		elif not os.WIFEXITED(status):
			import signal
			try:
				os.kill(pid, signal.SIGKILL)
			except OSError:
				pass

		es = report['exitstatus'] = os.WEXITSTATUS(status)
		metrics = test_metrics_signal(stop_time - start_time, report['fate'], rusage)
		stop_message = close_test_transaction(
			stop_time, test.identifier, pid,
			report['fate'], report.get('failure'),
			es, rusage,
		)
		self.log.emit(channel, metrics)
		self.log.emit(channel, stop_message)
		self.log.flush()
		return report

	def seal(self, test):
		# Usually ran within the fork.
		try:
			signal.signal(signal.SIGALRM, test.timeout)
			signal.alarm(8)

			test.seal()
		finally:
			signal.alarm(0)
			signal.signal(signal.SIGALRM, signal.SIG_IGN)

		faten = test.fate.subtype
		parts = test.identifier.split('.')
		if test.fate.impact >= 0:
			parts[1:] = [x for x in parts[1:]]
		else:
			parts[1:-1] = [x for x in parts[1:-1]]

		ident = '.'.join(parts)

		report = {
			'test': test.identifier,
			'impact': test.fate.impact,
			'fate': faten,
			'interrupt': None,
			'failure': None,
		}

		if test.fate.subtype == 'divide':
			ident = '/'.join((self.identity, test.identifier))
			subharness = self.__class__(ident, test.subject, test.fate.content)
			subharness.reveal()
		elif test.fate.impact < 0:
			report['failure'] = list(sequence_failure(test.fate.__cause__))

			if isinstance(test.fate.__cause__, (KeyboardInterrupt, BrokenPipeError)):
				report['interrupt'] = True
			self._print_tb(test.fate)
			return report

			import pdb
			# error cases chain the exception
			if test.fate.__cause__ is not None:
				tb = test.fate.__cause__.__traceback__
			else:
				tb = None
			if tb is None:
				tb = test.fate.__traceback__
			pdb.post_mortem(tb)
		return report

def intercept(product, project, intention):
	# Finder for test's target intention.
	from ...system import factors

	class ProjectFinder(factors.IntegralFinder):
		def find_spec(self, name, path, target=None):
			spec = None
			if name[:self.project_length] in self.project_set:
				spec = super().find_spec(name, path, target=target)
			if spec is None:
				return None

			if hasattr(spec.loader, '_bytecode'):
				image = spec.loader._bytecode
			else:
				image = spec.loader.path

			if not os.path.exists(image):
				# Exception is desired here as it is likely *not* desired to run
				# tests using the source loader's bytecode.
				raise ImportError("intention specific image not available for test")

			return spec

	# Mirror the default finder's configuration.
	sfif = ProjectFinder.create(
		factors.finder.python_bytecode_variants['system'],
		factors.finder.python_bytecode_variants['architecture'],
		factors.finder.extension_variants['architecture'],
		intention
	)
	sfif.connect(files.Path.from_absolute(product))
	sfif.project_set = {project, project + '.'}
	sfif.project_length = len(project) + 1
	sys.meta_path.insert(0, sfif)

def main(inv:process.Invocation) -> process.Exit:
	inv.imports(['FRAMECHANNEL', 'INTENTION', 'PROJECT', 'PRODUCT'])

	project, rfpath, *testslices = inv.args # Import target and start[:stop] tests.
	slices = []
	for s in testslices:
		if ':' in s:
			start, stop = s.split(':')
		else:
			start = s
			stop = ''
		slices.append((start or None, stop or None))

	channel = inv.environ.get('FRAMECHANNEL') or 'test'
	intention = inv.environ.get('INTENTION') or 'optimal'
	product = inv.environ.get('PRODUCT') or ''
	os.environ['PROJECT'] = project

	if product:
		# Add intercept for this project's modules.
		intercept(product, project, intention)

	module_path = '.'.join((project, rfpath))
	p = Harness.from_module(importlib.import_module(module_path), slices=slices)
	p.channel = channel
	p.status = sys.stderr
	p.log = frames.Log.stdout()

	p.log.emit(*open_factor_transaction(elapsed(), p.identity, channel=channel))
	p.log.flush()
	p.reveal()
	p.log.emit(*close_factor_transaction(elapsed(), p.identity, channel=channel))

	return inv.exit(0)

if __name__ == '__main__':
	with corefile.constraint(None):
		process.control(main, process.Invocation.system())
