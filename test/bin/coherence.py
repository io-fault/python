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
from ...status import python
from ...time.sysclock import elapsed
from ...transcript import metrics
from ...transcript.io import Log

from .. import engine
from .. import core

status_identifiers = {
	'explicit': 'skipped',
	'skip': 'skipped',
	'return': 'passed',
	'pass': 'passed',
	'fail': 'failed',
	'core': 'failed',
	'error': 'failed',
}

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
		def manage(harness=self, test=test):
			with test.exits:
				return harness.execute(test)
		pid, seal = self.concurrently(manage, waitpid=os.wait4)

		xact_metrics = metrics.Procedure(
			work=metrics.Work(1, 0, 0, 0),
			msg=metrics.Advisory(),
			usage=metrics.Resource(),
		)
		ext = {
			'@timestamp': [str(start_time)],
			'@type': ['system'],
			'@metrics': [xact_metrics.sequence()],
			'system-process-id': [str(pid)],
		}

		xid = '/'.join((self.project, self.factor, test.identifier))
		self.log.xact_open(xid, xid + ": dispatched", ext)
		self.log.flush()

		l = []

		report = seal(status_ref = l.append)
		try:
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
		finally:
			failure = None
			if report['fate'] == 'skip':
				work = metrics.Work(0, 0, 1, 0)
			elif report['impact'] < 0:
				work = metrics.Work(0, 0, 0, 1)
				failure = report.get('failure')
			else:
				work = metrics.Work(0, 1, 0, 0)

			# Construct metrics for reporting fate and resource usage.
			usage = metrics.Resource(
				1, int(rusage.ru_maxrss),
				# Nanosecond precision.
				int((rusage.ru_stime + rusage.ru_utime) * (10**9)),
				stop_time - start_time,
			)
			xact_metrics = metrics.Procedure(work=work, msg=metrics.Advisory(), usage=usage)

			ext = {
				'@timestamp': [str(stop_time)],
				'@metrics': [xact_metrics.sequence()],
				'fate': [report['fate']],
				'impact': [str(report['impact'])],
			}
			if failure:
				ext['@failure-image'] = ['python-exception']
				ext['@failure-image'].extend(x[:-1] for x in python.format(failure))

			fate = status_identifiers.get(report['fate'], 'unknown')
			self.log.xact_close(xid, xid + ": " + fate, ext)
			self.log.flush()

		return report

	def execute(self, test):
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
			ferror = test.fate.__cause__
			report['failure'] = list(python.failure(ferror, ferror.__traceback__))

			if isinstance(test.fate.__cause__, (KeyboardInterrupt, BrokenPipeError)):
				report['interrupt'] = True
			return report

			import pdb
			# error cases chain the exception
			if ferror is not None:
				tb = ferror.__traceback__
			else:
				tb = None
			pdb.post_mortem(tb or test.fate.__traceback__)
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
	sys.excepthook = python.hook
	inv.imports(['FRAMECHANNEL', 'INTENTION', 'PROJECT', 'PRODUCT'])

	project, rfpath, *testslices = inv.args # Import target and start[:stop] tests.
	slices = []
	for s in testslices:
		limit = None

		if ':' in s:
			start, stop = s.split(':')
			if stop.isdigit():
				limit = int(stop)
				stop = None
		else:
			# Require colon for slice.
			start = s
			stop = ''
			limit = 1

		slices.append((start or None, stop or None, limit))

	channel = inv.environ.get('FRAMECHANNEL') or None
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
	p.project = project
	p.factor = rfpath
	p.log = log = Log.stdout(channel=inv.environ.get('FRAMECHANNEL') or None)
	log.declare()

	xid = '/'.join((project, rfpath))
	ext = {
		'@timestammp': [str(elapsed())],
		'@work': [str(p.count)],
	}
	log.xact_open(xid, xid + ": sealing fates of " + str(p.count) + " tests", ext)
	log.flush()
	del ext

	p.reveal()
	ext = {
		'@timestammp': [str(elapsed())],
	}
	log.xact_close(xid, xid + ": fates revealed", ext)

	return inv.exit(0)

if __name__ == '__main__':
	with corefile.constraint(None):
		process.control(main, process.Invocation.system())
