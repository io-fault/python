"""
# Test the coherence of the specified project.
"""
import os
import sys
import gc
import contextlib
import signal
import functools
import types
import importlib
import resource

from ..system import corefile
from ..system import process
from ..system import files
from ..system import factors
from ..status import python
from ..time.system import elapsed
from ..transcript import metrics
from ..transcript.io import Log

from . import engine
from . import types

class Harness(engine.Harness):
	"""
	# The collection and execution of a series of tests.
	"""
	concurrently = staticmethod(process.concurrently)

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

	def _print_tb(self, test):
		import traceback
		tb = traceback.format_exception(test.exception.__class__, test.exception, test.traceback)
		tb = ''.join(tb)
		sys.stderr.write(tb)

	def dispatch(self, test):
		start_time = elapsed()

		# Test in a subprocess.
		def manage(harness=self, test=test):
			with test.exits:
				return harness.execute(test)

		mid = os.environ['METRICS_IDENTITY']
		os.environ['METRICS_IDENTITY'] += '/' + test.identifier
		pid, execute_test = self.concurrently(manage, waitpid=os.wait4)
		# Fork is raised here by concurrently, so don't set this in finally.
		os.environ['METRICS_IDENTITY'] = mid

		xact_metrics = metrics.Procedure(
			work=metrics.Work(1, 0, 0, 0),
			msg=metrics.Advisory(),
			usage=metrics.Resource(),
		)

		xid = '/'.join((self.project, self.factor, test.identifier))
		self.log.xact_open(xid, xid + ": dispatched", {
			'@timestamp': [str(start_time)],
			'@type': ['system'],
			'@metrics': [xact_metrics.sequence()],
			'system-process-id': [str(pid)],
		})
		self.log.flush()

		l = []

		report = execute_test(status_ref=l.append)
		try:
			stop_time = elapsed()

			if report is None:
				report = {
					'exception': None,
					'failure': types.FailureType.never,
					'conclusion': types.TestConclusion.failed,
					'metrics': {
						'processing': [],
						'memory': [],
						'contentions': 0,
					},
				}

			pid, status, rusage = l[0]

			if os.WCOREDUMP(status):
				report['failure'] = types.FailureType.fault
				self._handle_core(corefile.location(pid))
			elif not os.WIFEXITED(status):
				import signal
				try:
					os.kill(pid, signal.SIGKILL)
				except OSError:
					pass
		finally:
			failure = report.get('exception', None)
			if failure:
				fail_image = ['python-exception']
				fail_image.extend(x[:-1] for x in python.format(failure))
			else:
				fail_image = ()

			if report['conclusion'] == types.TestConclusion.skipped:
				work = metrics.Work(0, 0, 1, 0)
			elif report['conclusion'] == types.TestConclusion.failed:
				work = metrics.Work(0, 0, 0, 1)
			else:
				assert report['conclusion'] == types.TestConclusion.passed
				work = metrics.Work(0, 1, 0, 0)

			# Construct metrics.
			ut = int((rusage.ru_stime + rusage.ru_utime) * (10**9))
			rt = stop_time - start_time
			usage = metrics.Resource(1, int(rusage.ru_maxrss), ut, rt)
			xact_metrics = metrics.Procedure(work=work, msg=metrics.Advisory(), usage=usage)

			self.log.xact_close(xid, xid + ": " + report['conclusion'].name, {
				'@timestamp': [str(stop_time)],
				'@metrics': [xact_metrics.sequence()],
				'@failure-image': fail_image,
			})
			self.log.flush()

		report['failure-image'] = fail_image
		rm = report['metrics']
		rm['duration'] = rt
		rm['processing'].append(ut)
		rm['memory'].append(rusage.ru_maxrss)

		return report

	def test(self, test):
		"""
		# Execute the test function and configure the identified conclusion.
		"""

		try:
			r = test.function(test)
			# Make an attempt at causing any deletions.
			gc.collect()
		except types.Conclude as err:
			test.conclusion = err.conclusion
			test.failure = err.failure
			test.exception = err
		except types.Absurdity as err:
			test.conclusion = types.TestConclusion.failed
			test.failure = types.FailureType.absurdity
			test.exception = err
		except Exception as err:
			test.conclusion = types.TestConclusion.failed
			test.failure = types.FailureType.fault
			test.exception = err
		except BaseException as err:
			test.conclusion = types.TestConclusion.failed
			test.failure = types.FailureType.interrupt
			test.exception = err
		else:
			test.conclusion = types.TestConclusion.passed
			test.failure = types.FailureType.none
			test.exception = None
			test.traceback = None
			return

		# Remove the Harness.test (this) frame from the traceback.
		test.exception.__traceback__ = test.exception.__traceback__.tb_next

		# Record traceback for all conclusions except return.
		test.traceback = test.exception.__traceback__

	def execute(self, test, count=1):
		test.metrics['processing'] = []
		test.metrics['memory'] = []

		before = resource.getrusage(resource.RUSAGE_SELF)
		try:
			signal.signal(signal.SIGALRM, test._timeout)

			for i in range(count):
				signal.alarm(8)
				self.test(test)
		finally:
			# Disable alarm as soon as possible.
			signal.alarm(0)
			signal.signal(signal.SIGALRM, signal.SIG_IGN)
		after = resource.getrusage(resource.RUSAGE_SELF)

		test.metrics['executions'] = count

		# Deltas.
		ptime = (after.ru_stime + after.ru_utime) - (before.ru_stime + before.ru_utime)
		test.metrics['processing'].append(ptime * (10**9))
		test.metrics['memory'].append(after.ru_maxrss - before.ru_maxrss)

		# Final snapshot.
		test.metrics['processing'].append((after.ru_stime + after.ru_utime) * (10**9))
		test.metrics['memory'].append(after.ru_maxrss)

		report = {
			'test': test.identifier,
			'conclusion': test.conclusion,
			'failure': test.failure,
			'metrics': test.metrics,
			'exception': None,
		}

		if test.failure != types.FailureType.none:
			report['exception'] = list(python.failure(test.exception, test.traceback))
			return report
			import pdb
			pdb.post_mortem(test.traceback)
		return report

def intercept(product, project):
	# Use an independent finder for the test subjects.
	sfif = factors.IntegralFinder.create(
		factors.finder.python_bytecode_variants['system'],
		factors.finder.python_bytecode_variants['architecture'],
		factors.finder.system_extension_variants['architecture'],
	)
	sfif.connect(files.Path.from_absolute(product))
	sfif.project_set = {project, project + '.'}
	sfif.project_length = len(project) + 1
	sys.meta_path.insert(0, sfif)

def slicing(spec):
	limit = None

	if ':' in s:
		start, stop = spec.split(':')
		if stop.isdigit():
			limit = int(stop)
			stop = None
	else:
		# Require colon for slice.
		start = spec
		stop = ''
		limit = 1

	return (start or None, stop or None, limit)

def trapped_report(source):
	"""
	# Reform the report into the common join protocol.
	"""

	return [
		source.get('test', None), # Element Identity
		source['conclusion'].name,
		source['failure'].name,
		source['metrics'],
		source.get('status', None),
		source.get('exception') or [],
	]

def main(inv:process.Invocation) -> process.Exit:
	sys.excepthook = python.hook
	inv.imports([
		'FRAMECHANNEL', 'PROJECT', 'PRODUCT',
		'METRICS_CAPTURE',
		'METRICS_IDENTITY', 'DISPATCH_IDENTITY', 'PROCESS_IDENTITY',
	])

	project, rfpath, *testslices = inv.args # Factor and optional test identifiers.
	slices = list(map(slicing, testslices))

	xid = '/'.join((project, rfpath))

	channel = inv.environ.get('FRAMECHANNEL') or None
	product = inv.environ.get('PRODUCT') or ''
	pid = inv.environ.get('PROCESS_IDENTITY', None)

	if pid is None:
		# Conditionally initialize process identity.
		# PROCESS_IDENTITY is how parallel writes are supported when
		# capturing metrics. It must be unique across the processes
		# collecting data.
		if inv.environ.get('DISPATCH_IDENTITY', None):
			# If &fault.transcript controller is running the test.
			pid = inv.environ['DISPATCH_IDENTITY']
		else:
			pid = str(os.getpid())

	os.environ['PROJECT'] = project
	os.environ['PROCESS_IDENTITY'] = pid
	os.environ['METRICS_IDENTITY'] = xid

	if product:
		# Add intercept for this project's modules.
		factors.finder.connect(files.root@product)
		pd = factors.finder.context.connect(files.root@product)
		factors.finder.context.load()
		for x in pd.connections:
			factors.finder.connect(x)
		intercept(product, project)

	log = Log.stdout(channel=channel)
	log.declare()

	module_path = '.'.join((project, rfpath))
	tm = importlib.import_module(module_path)

	# When configured in the target module, write the test reports.
	rtrap = getattr(tm, '__metrics_trap__', None)
	if rtrap is not None:
		rpath = (files.root@rtrap)/'test'/'.fault-test-reports'
	else:
		rpath = None

	h = Harness.from_module(tm, slices=slices)
	h.status = sys.stderr
	h.project = project
	h.factor = rfpath
	h.log = log

	open_msg = xid + ": harness selected " + str(h.count) + " tests for analysis."
	log.xact_open(xid, open_msg, {
		'@timestammp': [str(elapsed())],
		'@work': [str(h.count)],
	})
	log.flush()
	del open_msg

	if rpath is not None:
		# Write a copy of the test reports to the metrics trap.
		reports = list(map(trapped_report, h.execute_tests()))
		contentions = sum(x[3]['contentions'] for x in reports)
		test_count = len(reports)

		import json
		rpath.fs_alloc()
		with rpath.fs_open('w') as f:
			json.dump(reports, f)
	else:
		test_count = 0
		contentions = 0
		for tr in h.execute_tests():
			test_count += 1
			contentions += tr['metrics']['contentions']

	close_msg = xid + ": %d contentions across %d tests." %(contentions, test_count,)
	log.xact_close(xid, close_msg, {
		'@timestammp': [str(elapsed())],
	})
	del close_msg

	return inv.exit(0)

if __name__ == '__main__':
	with corefile.constraint(None):
		process.control(main, process.Invocation.system())
