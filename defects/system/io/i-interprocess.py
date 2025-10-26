import os
import sys
import traceback
from . import common

def child_echo(am, objects):
	"""
	# Echos objects received back at the sender.
	"""

	for x in am.delta():
		# continually echo the received objects until termination
		if objects.read_channel.terminated:
			# expecting to be killed by receiving a None object.
			objects.read_channel.port.raised()

		if objects.write_channel.terminated:
			break

		if objects.received_objects and objects.write_channel.exhausted:
			if objects.received_objects[0] is None:
				# terminate on None, break on next loop.
				objects.write_channel.terminate()
			else:
				objects.send(objects.received_objects[0])
				del objects.received_objects[0]

def fork_and_circulate(test, am, channels):
	# fork before am.manage() for ease.
	pid = os.fork()
	if pid == 0:
		exit_status = 0
		sys.stdout.close()
		try:
			objects = common.Objects(channels[2:])
			# Parent's ports.
			channels[0].port.shatter()
			channels[1].port.shatter()

			with am.thread(), am.manage(objects):
				child_echo(am, objects)
		except:
			traceback.print_exc(file=sys.stderr)
			exit_status = 7
		finally:
			os._exit(exit_status)
	else:
		parent = common.Objects(channels[:2])
		echos = [
			2,
			3,
			[x**2 for x in range(200)],
			"foo",
			"bar",
			"data!" * 200,
		]

		with am.thread(), am.manage(parent):
			# Child's ports.
			channels[2].port.shatter()
			channels[3].port.shatter()

			for echo in echos:
				parent.send(echo)
				for x in am.delta():
					# Reading.
					if parent.received_objects:
						break
				test/echo == parent.received_objects[0]
				parent.clear() # Can't be racing. Nothing is being written.
			else:
				parent.send(None)
				for x in am.delta():
					if parent.read_channel.terminated:
						break
				parent.write_channel.terminate()
		test/parent.channels[0].terminated == True
		test/parent.channels[1].terminated == True

		_pid, code = os.waitpid(pid, 0)
		test/os.WEXITSTATUS(code) == 0

def test_bidirectional(test):
	"""
	# Check for IPC via bidirectional kernel ports.
	"""

	am = common.ArrayActionManager()
	channels = common.allocsockets(am.array)
	fork_and_circulate(test, am, channels)

def test_unidirectional(test):
	"""
	# Check for IPC via unidirectional kernel ports.
	"""

	am = common.ArrayActionManager()

	r, w = common.allocpipe(am.array)
	rr, ww = common.allocpipe(am.array)

	channels = (r, ww, rr, w)
	fork_and_circulate(test, am, channels)
