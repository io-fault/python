import io
import os

def perform_cat(pids, input, output, data, *errors):
	error = []
	for errfd in errors:
		error.append(io.open(errfd, mode='rb'))

	input = io.open(input, mode='wb')
	output = io.open(output, mode='rb')

	idata = data
	while idata:
		idata = idata[input.write(idata):]

	input.flush()
	input.close()

	out = b''
	while out != data:
		out += output.read(len(data) - len(out))

	for e in error:
		e.close()

	status = []

	# Workaround for macos.
	# Process (cat) exits don't appear to be occurring properly
	# on macos. (Thu Jun 22 09:33:35 MST 2017)
	# Specifically, the cat implementation doesn't appear to be getting
	# closed file descriptors.
	# This may indicate an issue with the fault.system or its usage.
	for pid in pids:
		os.kill(pid, 9)

	for pid in pids:
		r = os.waitpid(pid, 0)
		status.append(r)
	output.close()

	return data, status
