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

status_identifiers = {
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
				report = {
					'fate': 'unknown',
					'impact': -1,
					'interrupt': None,
					'metrics': {
						'processing': [],
						'memory': [],
					},
				}

			pid, status, rusage = l[0]

			if os.WCOREDUMP(status):
				faten = 'core'
				report['fate'] = 'core'
				test.fate = types.Fate('process core dump', subtype='core')
				self._handle_core(corefile.location(pid))
			elif not os.WIFEXITED(status):
				import signal
				try:
					os.kill(pid, signal.SIGKILL)
				except OSError:
					pass
		finally:
			failure = report.get('failure', None)
			if failure:
				fail_image = ['python-exception']
				fail_image.extend(x[:-1] for x in python.format(failure))
			else:
				fail_image = ()

			if report['fate'] == 'skip':
				work = metrics.Work(0, 0, 1, 0)
			elif report['impact'] < 0:
				work = metrics.Work(0, 0, 0, 1)
			else:
				work = metrics.Work(0, 1, 0, 0)

			# Construct metrics for reporting fate and resource usage.
			ut = int((rusage.ru_stime + rusage.ru_utime) * (10**9))
			rt = stop_time - start_time
			usage = metrics.Resource(1, int(rusage.ru_maxrss), ut, rt)
			xact_metrics = metrics.Procedure(work=work, msg=metrics.Advisory(), usage=usage)

			ext = {
				'@timestamp': [str(stop_time)],
				'@metrics': [xact_metrics.sequence()],
				'@failure-image': fail_image,
				'fate': [report['fate']],
				'impact': [str(report['impact'])],
			}

			fate = status_identifiers.get(report['fate'], 'unknown')
			self.log.xact_close(xid, xid + ": " + fate, ext)
			self.log.flush()

		report['failure-image'] = fail_image
		rm = report['metrics']
		rm['duration'] = rt
		rm['processing'].append(ut)
		rm['memory'].append(rusage.ru_maxrss)
		return report

	def execute(self, test, count=1):
		os.environ['METRICS_IDENTITY'] += '/' + test.identifier
		test.metrics['processing'] = []
		test.metrics['memory'] = []

		before = resource.getrusage(resource.RUSAGE_SELF)
		try:
			signal.signal(signal.SIGALRM, test.timeout)

			for i in range(count):
				signal.alarm(8)
				test.seal()
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
			'metrics': test.metrics,
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
		source['impact'],
		source['fate'],
		source['metrics'],
		source.get('status', None),
		source.get('failure') or [],
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
		rpath = (files.root@rtrap)/'test'/'.fault-test-fates'
	else:
		rpath = None

	p = Harness.from_module(tm, slices=slices)
	p.status = sys.stderr
	p.project = project
	p.factor = rfpath
	p.log = log
	ext = {
		'@timestammp': [str(elapsed())],
		'@work': [str(p.count)],
	}
	log.xact_open(xid, xid + ": sealing fates of " + str(p.count) + " tests", ext)
	log.flush()
	del ext

	if rpath is not None:
		reports = list(map(trapped_report, p.reveal()))
		import json
		rpath.fs_alloc()
		with rpath.fs_open('w') as f:
			json.dump(reports, f)
	else:
		for tr in p.reveal():
			pass

	ext = {
		'@timestammp': [str(elapsed())],
	}
	log.xact_close(xid, xid + ": fates revealed", ext)

	return inv.exit(0)

if __name__ == '__main__':
	with corefile.constraint(None):
		process.control(main, process.Invocation.system())
